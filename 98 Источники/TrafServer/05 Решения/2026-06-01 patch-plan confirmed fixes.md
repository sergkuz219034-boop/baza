# 2026-06-01 patch-plan confirmed fixes

## Цель

Свести подтверждённые первопричины к минимальному и безопасному набору правок без лишней смены архитектуры.

## Порядок внедрения

1. Security и auth:
   - `docker-compose.yml`
   - `AccountManager/api/main.py`
   - `deploy/Caddyfile` при решении включать perimeter basic auth
2. Прикладная корректность:
   - `api/routers/settings.py`
3. Runtime lifecycle:
   - `main.py`
   - `services/leads_service.py`
4. Observability:
   - `api/routers/jobs.py`
   - при необходимости `api/server.py`

## Patch 1. Убрать дефолтный secret и fail-open в Account Manager

### Файлы

- `docker-compose.yml`
- `AccountManager/api/main.py`

### Проблема

- Дефолтный `SESSION_SECRET_KEY` допускает предсказуемую подпись JWT.
- При пустом secret middleware работает по fail-open логике.

### Предлагаемое изменение

```diff
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@
-      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY:-JhB8kdm94VEAFub4YV57rKX5EXMUA8jDlADeaZGybs6I6jrAb3U-xo_Y6uhL2UUx}
+      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
```

```diff
--- a/AccountManager/api/main.py
+++ b/AccountManager/api/main.py
@@
-        if not secret:
-            return await call_next(request)  # fallback если ключ не настроен
+        if not secret:
+            logger.error("SESSION_SECRET_KEY is not configured")
+            return JSONResponse(
+                status_code=503,
+                content={"detail": "Auth is not configured"},
+            )
```

### Почему безопасно

- Меняется только небезопасный fallback.
- Корректно настроенное окружение продолжит работать без изменения бизнес-логики.

### Побочные эффекты

- Неправильно настроенные окружения начнут падать явно, а не тихо обходить auth.

## Patch 2. Починить owner binding в destructive settings endpoints

### Файл

- `api/routers/settings.py`

### Проблема

- Часть endpoint'ов очистки не передаёт owner context в `utils.database.clear_*`.

### Предлагаемое изменение

Применить один и тот же паттерн для:

- `/db/autofit`
- `/db/leads`
- `/db/send-history`
- `/db/invite-history`
- `/db/retry-queue`
- `/db/run-log`

Пример:

```diff
--- a/api/routers/settings.py
+++ b/api/routers/settings.py
@@
-def clear_leads_endpoint(_: AccessPrincipal = Depends(require_operator)):
+def clear_leads_endpoint(principal: AccessPrincipal = Depends(require_operator)):
     try:
-        count = clear_leads()
+        with bind_current_username(principal.username):
+            count = clear_leads()
         return {"ok": True, "message": f"Лиды очищены ({count} записей удалено)", "deleted": count}
```

### Почему безопасно

- Используется уже существующий паттерн из `DELETE /db`.
- Не меняется схема БД и не меняется модель доступа, только восстанавливается ожидаемое owner-scoped поведение.

### Побочные эффекты

- API начнёт реально удалять данные текущего пользователя, а не возвращать ложный `ok`.

## Patch 3. Сделать shutdown действительно graceful

### Файлы

- `main.py`
- `services/leads_service.py`

### Проблема

- `main.py` немедленно делает `sys.exit(0)` после `stop_event.set()`.
- `run_server_mode()` не выходит из основного loop по stop-сигналу.
- scheduler-thread daemon'ный.

### Предлагаемое изменение

```diff
--- a/main.py
+++ b/main.py
@@
-    def _graceful_handler(signum, frame):
+    def _graceful_handler(signum, frame):
         print(Fore.YELLOW + "\n [!] Получен сигнал завершения — ожидаем окончания текущей работы...")
         try:
             from utils.state import stop_event
             stop_event.set()
         except Exception:
             logger.exception("Error during graceful shutdown")
-        sys.exit(0)
+
+        try:
+            if scheduler_thread.is_alive():
+                scheduler_thread.join(timeout=35)
+        except Exception:
+            logger.exception("Failed while waiting scheduler thread to stop")
+
+        sys.exit(0)
@@
-    scheduler_thread = threading.Thread(target=run_server_mode, args=(config,), daemon=True)
+    scheduler_thread = threading.Thread(target=run_server_mode, args=(config,), daemon=False)
```

```diff
--- a/services/leads_service.py
+++ b/services/leads_service.py
@@
-        while True:
+        while not is_stop_requested():
@@
-            _time_module.sleep(30)
+            if is_stop_requested():
+                break
+            _time_module.sleep(30)
```

### Почему безопасно

- Не меняется бизнес-логика цикла.
- Меняется только жизненный цикл остановки и ожидание завершения фонового потока.

### Побочные эффекты

- Контейнер будет останавливаться чуть дольше, если идёт активная работа.
- Может вскрыть скрытые долгие операции, которые раньше просто обрывались.

## Patch 4. Сделать WS-уведомления о статусе jobs надёжнее

### Файл

- `api/routers/jobs.py`

### Проблема

- `_broadcast_ws()` полагается на `asyncio.get_event_loop()` в sync/thread-коде.
- Исключения проглатываются.

### Минимальный безопасный вариант

- Не пытаться доставлять события из произвольного потока через случайный loop.
- Либо хранить ссылку на основной loop в модуле/состоянии приложения, либо оставить `_push_status_loop()` как основной источник статуса и логировать сбои событийного пуша явно.

Вариант с минимальным вмешательством:

```diff
--- a/api/routers/jobs.py
+++ b/api/routers/jobs.py
@@
 def _broadcast_ws(data: dict) -> None:
     try:
         import asyncio
-
         from api.ws_manager import ws_manager
+        from api.server import _ws_handler
-
-        loop = asyncio.get_event_loop()
-        if loop.is_running():
-            asyncio.run_coroutine_threadsafe(ws_manager.broadcast_status(data), loop)
-    except Exception:
-        pass
+        loop = getattr(_ws_handler, "_loop", None) if _ws_handler is not None else None
+        if loop is not None and loop.is_running():
+            asyncio.run_coroutine_threadsafe(ws_manager.broadcast_status(data), loop)
+        else:
+            logger.debug("WS status broadcast skipped: no running event loop")
+    except Exception:
+        logger.exception("WS status broadcast failed")
```

### Почему безопасно

- Используется уже установленный loop из `WebSocketLogHandler`.
- Ошибки больше не исчезают бесследно.

### Побочные эффекты

- Появятся диагностические логи там, где раньше была тишина.
- Есть техническая связность с `api.server._ws_handler`, но она мала и контролируема.

## Patch 5. Сделать import secrets неразрушающим

### Файл

- `api/routers/settings.py`

### Проблема

- `_write_imported_secret_files()` удаляет все текущие secret-файлы, которых нет в payload.

### Предлагаемое изменение

- Ввести whitelist управляемых файлов, например:
  - `rabota_tokens.json`
  - `service_account.json`
- Не трогать прочие файлы в `secrets/`.

```diff
--- a/api/routers/settings.py
+++ b/api/routers/settings.py
@@
+_MANAGED_IMPORT_SECRET_FILES = {"rabota_tokens.json", "service_account.json"}
@@
-    for stale_name in existing - incoming:
+    for stale_name in (existing - incoming):
+        if stale_name not in _MANAGED_IMPORT_SECRET_FILES:
+            continue
         try:
             (secrets_dir / stale_name).unlink()
         except FileNotFoundError:
             pass
```

### Почему безопасно

- Сужается область destructive поведения.
- Runtime и посторонние auth-файлы не будут удаляться случайно.

### Побочные эффекты

- Старые неуправляемые secrets останутся на месте, если их надо было вычищать автоматически.

## Patch 6. Устранить security drift в reverse proxy

### Файлы

- `deploy/Caddyfile`
- возможно `docker-compose.yml`

### Варианты

1. Включить `basic_auth` и для `ACCOUNT_MANAGER_DOMAIN`.
2. Или удалить `ACCOUNT_MANAGER_BASIC_AUTH_*` из compose как мёртвую конфигурацию.

### Предпочтение

Если perimeter auth действительно нужен:

```diff
--- a/deploy/Caddyfile
+++ b/deploy/Caddyfile
@@
 {$ACCOUNT_MANAGER_DOMAIN:am.traffic-hubcrm.ru} {
 	encode zstd gzip
+
+	basic_auth {
+		{$ACCOUNT_MANAGER_BASIC_AUTH_USER} {$ACCOUNT_MANAGER_BASIC_AUTH_HASH}
+	}
 
 	reverse_proxy account_manager:8000 {
 		header_down -Server
 	}
```

### Почему безопасно

- Не меняет внутреннюю JWT-модель.
- Даёт дополнительный периметр, который уже ожидался по compose-переменным.

### Побочные эффекты

- Понадобится корректно настроить хэш пароля в окружении.
- Может затронуть существующие прямые интеграции, если они ходят без basic auth.

## Проверка после внедрения

1. `AccountManager`:
   - не стартует или отвечает конфигурационной ошибкой без `SESSION_SECRET_KEY`
   - не принимает токен, подписанный известным дефолтным secret
2. `settings` clear-endpoints:
   - реально удаляют owner-scoped данные и возвращают ненулевой `deleted`, когда данные есть
3. `shutdown`:
   - при `SIGTERM` нет мгновенного обрыва scheduler loop
   - поток планировщика корректно завершается
4. `WS status`:
   - UI получает `job_start/job_done/job_error`
   - при проблеме с loop есть явный debug/error лог
5. `settings import`:
   - `service_account.json` и `rabota_tokens.json` импортируются
   - посторонние secrets остаются нетронутыми

## Примечание

Этот patch-plan основан только на подтверждённых проблемах. Он сознательно не включает более широкие архитектурные переработки, чтобы не лечить проект “с запасом” там, где пока достаточно точечных исправлений.
