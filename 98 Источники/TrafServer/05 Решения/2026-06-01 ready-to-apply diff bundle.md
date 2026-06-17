# 2026-06-01 ready-to-apply diff bundle

## Назначение

Единый пакет подтверждённых точечных правок по результатам расследования.

Этот документ не применяет изменения автоматически. Он нужен как инженерный diff-bundle для безопасного внедрения в прод-код после отдельной валидации.

## Patch A. Account Manager: убрать дефолтный secret

### Файл

- `docker-compose.yml`

### Diff

```diff
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@
-      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY:-JhB8kdm94VEAFub4YV57rKX5EXMUA8jDlADeaZGybs6I6jrAb3U-xo_Y6uhL2UUx}
+      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
```

### Обоснование

- убирает предсказуемый JWT secret;
- заставляет окружение явно задавать секрет.

### Побочные эффекты

- плохо настроенные окружения перестанут запускаться “по счастливой случайности”.

## Patch B. Account Manager: fail-open -> fail-closed

### Файл

- `AccountManager/api/main.py`

### Diff

```diff
--- a/AccountManager/api/main.py
+++ b/AccountManager/api/main.py
@@
     try:
         secret = os.environ.get("SESSION_SECRET_KEY", "")
-        if not secret:
-            return await call_next(request)  # fallback если ключ не настроен
+        if not secret:
+            logger.error("SESSION_SECRET_KEY is not configured")
+            return JSONResponse(
+                status_code=503,
+                content={"detail": "Auth is not configured"},
+            )
         payload = jwt.decode(token, secret, algorithms=["HS256"])
```

### Обоснование

- authentication больше не отключается при конфигурационной ошибке;
- проблема становится явной и диагностируемой.

### Побочные эффекты

- окружение с пустым secret начнёт отдавать ошибку вместо тихого bypass.

## Patch C. Settings API: owner binding для destructive endpoints

### Файл

- `api/routers/settings.py`

### Diff

```diff
--- a/api/routers/settings.py
+++ b/api/routers/settings.py
@@
-def clear_autofit_seen_endpoint(_: AccessPrincipal = Depends(require_operator)):
+def clear_autofit_seen_endpoint(principal: AccessPrincipal = Depends(require_operator)):
     try:
-        count = clear_autofit_seen()
+        with bind_current_username(principal.username):
+            count = clear_autofit_seen()
         return {"ok": True, "message": f"autofit_seen очищена ({count} записей удалено)", "deleted": count}
@@
-def clear_leads_endpoint(_: AccessPrincipal = Depends(require_operator)):
+def clear_leads_endpoint(principal: AccessPrincipal = Depends(require_operator)):
     try:
-        count = clear_leads()
+        with bind_current_username(principal.username):
+            count = clear_leads()
         return {"ok": True, "message": f"Лиды очищены ({count} записей удалено)", "deleted": count}
@@
-def clear_send_history_endpoint(_: AccessPrincipal = Depends(require_operator)):
+def clear_send_history_endpoint(principal: AccessPrincipal = Depends(require_operator)):
     try:
-        count = clear_send_history()
+        with bind_current_username(principal.username):
+            count = clear_send_history()
         return {"ok": True, "message": f"История рассылок очищена ({count} записей удалено)", "deleted": count}
@@
-def clear_invite_history_endpoint(_: AccessPrincipal = Depends(require_operator)):
+def clear_invite_history_endpoint(principal: AccessPrincipal = Depends(require_operator)):
     try:
-        count = clear_invite_history()
+        with bind_current_username(principal.username):
+            count = clear_invite_history()
         return {"ok": True, "message": f"История приглашений очищена ({count} записей удалено)", "deleted": count}
@@
-def clear_retry_queue_endpoint(_: AccessPrincipal = Depends(require_operator)):
+def clear_retry_queue_endpoint(principal: AccessPrincipal = Depends(require_operator)):
     try:
-        count = clear_retry_queue()
+        with bind_current_username(principal.username):
+            count = clear_retry_queue()
         return {"ok": True, "message": f"Очередь повторов очищена ({count} записей удалено)", "deleted": count}
@@
-def clear_run_log_endpoint(_: AccessPrincipal = Depends(require_operator)):
+def clear_run_log_endpoint(principal: AccessPrincipal = Depends(require_operator)):
     try:
-        count = clear_run_log()
+        with bind_current_username(principal.username):
+            count = clear_run_log()
         return {"ok": True, "message": f"Логи запусков очищены ({count} записей удалено)", "deleted": count}
```

### Обоснование

- приводит поведение в соответствие с уже корректным `/db`;
- исправляет подтверждённый дефект “API ответил ok, но ничего не очистил”.

### Побочные эффекты

- endpoints начнут реально удалять owner-scoped данные пользователя.

## Patch D. Graceful shutdown: убрать мгновенный обрыв

### Файлы

- `main.py`
- `services/leads_service.py`

### Diff

```diff
--- a/main.py
+++ b/main.py
@@
     def _graceful_handler(signum, frame):
         print(Fore.YELLOW + "\n [!] Получен сигнал завершения — ожидаем окончания текущей работы...")
         try:
             from utils.state import stop_event
             stop_event.set()
         except Exception:
             logger.exception("Error during graceful shutdown")
-        sys.exit(0)
+        try:
+            if scheduler_thread.is_alive():
+                scheduler_thread.join(timeout=35)
+        except Exception:
+            logger.exception("Failed while waiting scheduler thread to stop")
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

### Обоснование

- внешний restart контейнера перестаёт рвать фоновые задачи мгновенно;
- код становится согласован с собственным сообщением “ожидаем окончания текущей работы”.

### Побочные эффекты

- остановка контейнера может занять дольше;
- может вскрыть операции, которые раньше обрывались без следа.

## Patch E. WS status delivery: сделать отправку диагностируемой

### Файл

- `api/routers/jobs.py`

### Diff

```diff
--- a/api/routers/jobs.py
+++ b/api/routers/jobs.py
@@
 def _broadcast_ws(data: dict) -> None:
     try:
         import asyncio
 
         from api.ws_manager import ws_manager
+        from api.server import _ws_handler
 
-        loop = asyncio.get_event_loop()
-        if loop.is_running():
+        loop = getattr(_ws_handler, "_loop", None) if _ws_handler is not None else None
+        if loop is not None and loop.is_running():
             asyncio.run_coroutine_threadsafe(ws_manager.broadcast_status(data), loop)
-    except Exception:
-        pass
+        else:
+            logger.debug("WS status broadcast skipped: no running event loop")
+    except Exception:
+        logger.exception("WS status broadcast failed")
```

### Обоснование

- устраняет тихую потерю статусов;
- использует уже существующий активный loop из websocket logging setup.

### Побочные эффекты

- добавит диагностические логи при сбоях;
- создаёт небольшую связность с `api.server._ws_handler`.

## Patch F. Import secrets: ограничить destructive delete

### Файл

- `api/routers/settings.py`

### Diff

```diff
--- a/api/routers/settings.py
+++ b/api/routers/settings.py
@@
+_MANAGED_IMPORT_SECRET_FILES = {"rabota_tokens.json", "service_account.json"}
@@
 def _write_imported_secret_files(files: dict[str, dict]) -> None:
@@
     for stale_name in existing - incoming:
+        if stale_name not in _MANAGED_IMPORT_SECRET_FILES:
+            continue
         try:
             (secrets_dir / stale_name).unlink()
         except FileNotFoundError:
             pass
```

### Обоснование

- сохраняет посторонние runtime/auth secrets;
- делает import предсказуемым и менее разрушительным.

### Побочные эффекты

- старые “неуправляемые” secrets будут оставаться в каталоге.

## Patch G. Reverse proxy: убрать drift или включить perimeter auth

### Файлы

- `deploy/Caddyfile`
- возможно `docker-compose.yml`

### Вариант 1: реально включить basic auth для Account Manager

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

### Вариант 2: удалить мёртвые переменные из compose

Если perimeter auth не нужен, то безопаснее убрать из `docker-compose.yml`:

- `ACCOUNT_MANAGER_BASIC_AUTH_USER`
- `ACCOUNT_MANAGER_BASIC_AUTH_HASH`

### Обоснование

- устраняет рассинхрон между ожидаемой и фактической защитой периметра.

## Порядок применения

1. Patch A + Patch B
2. Patch C
3. Patch D
4. Patch E
5. Patch F
6. Patch G

## Минимальная проверка после применения

### Security

- `AccountManager` не работает с пустым secret.
- Известный дефолтный secret больше не применим.

### Correctness

- `/db/leads`, `/db/send-history`, `/db/retry-queue`, `/db/run-log` реально очищают owner-scoped данные.

### Runtime

- при внешнем restart контейнера scheduler завершает цикл контролируемо.

### Observability

- UI получает `job_start/job_done/job_error`.

### Config safety

- import settings не удаляет посторонние secrets.
