# Debugging

Теги: #плейбук

## Как начинать расследование

1. Определить подсистему: runtime, dashboard API, TrafficHub, License Auth, AccountManager, deployment.
2. Проверить, есть ли исходник в `remote_server_snapshot` или только в `remote_files`.
3. Если проблема tenant-related, сначала открыть `remote_files/tests/test_traffic_tenant_isolation.py`.
4. Если проблема operational, проверить `main.py`, `jobs.py`, `settings.py`, `utils/database.py`.
5. Если проблема auth, проверить `api/authz.py`, `traffic_hub/api/deps.py`, `AccountManager/api/main.py`, compose env и Caddy.

## Быстрая проверка полного цикла

Если пользователь нажал **Полный цикл**, а в консоли видно только старт запуска:

1. Сразу проверить `traffichub_worker` live-лог.
2. Ищем точку обрыва:
   - если есть `▶ Фаза 1` и `▶ Фаза 2`, но нет продолжения, значит проблема в runtime job path;
   - если worker падает на `ImportError`/`AttributeError`, сверить актуальный helper API и серверный runtime;
   - если job state остался в `error`, сбросить owner-scoped состояние отдельно от логов и повторить запуск.
3. Для full cycle в актуальном состоянии системы критичный helper Sheets — `upload_to_sheets`, а не legacy-импорты.

## Полезные локальные артефакты

- `tools/inspect_*.py`
- `tools/remote_exec.py`
- `tools/push_fix.py`
- `remote_files/`
- `remote_server_snapshot/`

Runtime/state артефакты после миграции больше не лежат в корне vault. Если для расследования нужны локальные БД или кэшированные runtime-файлы, сначала проверяйте внешнее техническое хранилище:

- `C:\Users\Арт\Desktop\TrafServer_storage`
- `C:\Users\Арт\Desktop\TrafServer_runtime`

## Связанные заметки

- [[Overview]]
- [[Monitoring]]
- [[Documentation synchronization contract]]
