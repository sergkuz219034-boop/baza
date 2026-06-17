# Revalidation текущего server snapshot

Дата: 2026-06-01
Источник истины: `C:\Users\Арт\Desktop\TrafServer\remote_server_snapshot`

## Итог

Часть ранее подтверждённых проблем уже исправлена в текущем коде сервера и не должна больше считаться активной без дополнительного опровержения. Исторические заметки остаются полезными как forensic trail, но их нельзя читать как описание текущего состояния без этой пере-проверки.

## Уже исправлено в текущем snapshot

### 1. Graceful shutdown

- `main.py`
  - обработчик сигнала теперь не делает немедленный `sys.exit(0)` после `stop_event.set()`;
  - перед выходом выполняется `scheduler_thread.join(timeout=35)`;
  - `scheduler_thread` запускается как `daemon=False`.
- `services/leads_service.py`
  - главный цикл `run_server_mode()` завершает работу по `is_stop_requested()`.

Вывод: дефект "fake graceful shutdown" в текущем snapshot выглядит исправленным.

### 2. Owner binding в destructive settings endpoints

- `api/routers/settings.py`
  - `clear_autofit_seen`
  - `clear_leads`
  - `clear_send_history`
  - `clear_invite_history`
  - `clear_retry_queue`
  - `clear_run_log`

Все перечисленные endpoints в snapshot уже обёрнуты в `with bind_current_username(principal.username):`.

Вывод: ранее подтверждённая первопричина ложного `ok` без очистки owner-scoped данных, по текущему snapshot, исправлена.

### 3. AccountManager fail-open auth

- `AccountManager/api/main.py`
  - при пустом `SESSION_SECRET_KEY` middleware больше не пропускает запрос;
  - вместо этого пишет ошибку в лог и возвращает `503 Auth is not configured`.

Вывод: fail-open поведение исправлено.

### 4. Дефолтный secret у AccountManager

- `docker-compose.yml`
  - для `account_manager` используется `SESSION_SECRET_KEY=${SESSION_SECRET_KEY}` без встроенного fallback-значения.

Вывод: известный статический compose fallback в текущем snapshot устранён.

### 5. Destructive import secrets

- `api/routers/settings.py`
  - добавлен `_MANAGED_IMPORT_SECRET_FILES = {"rabota_tokens.json", "service_account.json"}`;
  - удаление при import теперь ограничено этим whitelist.

Вывод: прежнее destructive-by-default поведение уже смягчено.

### 6. WS broadcast деградация

- `api/routers/jobs.py`
  - код больше не делает слепой `asyncio.get_event_loop()` из thread/sync-кода;
  - используется loop, привязанный к `api.server._ws_handler`, если он активен;
  - ошибки больше не проглатываются молча, а логируются через `logger.exception(...)`.

Вывод: самая опасная часть прежней проблемы устранена. Надёжность стоит ещё проверять интеграционно, но старая первопричина уже ослаблена/исправлена.

## Всё ещё выглядит открытым

### 1. Root SSH по паролю на сервере

Серверная сторона проблемы остаётся актуальной:

- доступ осуществляется под `root`;
- operational-модель по-прежнему завязана на password auth;
- ранее подтверждались brute-force попытки в `sshd`.

Вывод: это остаётся `Critical` на стороне сервера.

### 2. Plaintext credentials в workspace-коде

Изначально открытые креды были зашиты в:

- `C:\Users\Арт\Desktop\TrafServer\tools\remote_exec.py`
- `C:\Users\Арт\Desktop\TrafServer\tools\push_fix.py`
- `C:\Users\Арт\Desktop\TrafServer\tools\fix_processed_sheet_status.py`
- `C:\Users\Арт\Desktop\TrafServer\tools\inspect_processed_sheet.py`
- `C:\Users\Арт\Desktop\TrafServer\tools\inspect_user_configs.py`
- `C:\Users\Арт\Desktop\TrafServer\150.241.70.31\README.md`

Теперь локальный workspace приведён в безопаснейшее состояние:

- пароль убран из кода и из server README;
- SSH-утилиты переведены на переменные окружения `TRAFSERVER_HOST`, `TRAFSERVER_USER`, `TRAFSERVER_PASSWORD`;
- для внешнего vendored runtime добавлен helper `tools/local_ssh.py`;
- helper подхватывает `paramiko` из внешних runtime-каталогов, больше не требуя держать их внутри Obsidian vault.

Проверка:

- рекурсивный поиск по workspace больше не находит прежний plaintext password;
- `local_ssh.ensure_paramiko()` успешно импортирует `paramiko`;
- изменённые SSH-утилиты компилируются без синтаксических ошибок.

Вывод: риск хранения root-пароля в workspace-коде локально закрыт, но серверная auth-модель всё ещё остаётся критической.

### 3. Security drift в reverse proxy

- `deploy/Caddyfile`
  - для `ACCOUNT_MANAGER_DOMAIN` по-прежнему нет `basic_auth`;
- `docker-compose.yml`
  - переменные `ACCOUNT_MANAGER_BASIC_AUTH_USER/HASH` по-прежнему объявлены.

Вывод: остаётся конфигурационный drift. Нужно либо реально включить auth в `Caddyfile`, либо удалить мёртвую конфигурацию из compose и документации.

## Что нужно скорректировать в предыдущих выводах

Исторические документы:

- `2026-06-01 подтверждённые первопричины runtime и security.md`
- `2026-06-01 patch-plan confirmed fixes.md`
- `2026-06-01 consolidated root-cause report.md`
- `2026-06-01 ready-to-apply diff bundle.md`

следует читать так:

- security findings про серверный SSH и perimeter drift остаются актуальными;
- часть code-level fixes из patch-plan уже фактически присутствует в текущем snapshot;
- повторное применение этих патчей без сверки с сервером теперь недопустимо.

## Текущий безопасный следующий шаг

1. Не пытаться повторно накатывать уже присутствующие правки.
2. Отдельно закрыть `Critical` вокруг root SSH на стороне сервера.
3. Отдельно решить, нужен ли `basic_auth` на `ACCOUNT_MANAGER_DOMAIN`, или compose/env нужно упростить.
4. Если потребуется внедрение, делать его уже от `remote_server_snapshot`, а не от старых заметок.
