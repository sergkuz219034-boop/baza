# 2026-06-16 Восьмой шаг PostgreSQL-aware maintenance

## Симптом

После переноса active runtime-таблиц в PostgreSQL функции обслуживания `clear_entire_database()` и `prune_old_data()` всё ещё вызывали SQLite-only модуль `utils/runtime_store_maintenance.py`.

Это опасно: UI/API могли показывать успешную очистку, но фактические production-данные уже находятся в PostgreSQL.

## Зона системы

- `utils/database.py`
- `utils/runtime_store_maintenance.py`
- новый `utils/runtime_store_pg_maintenance.py`
- PostgreSQL runtime tables:
  - `autolead_leads`;
  - `autolead_send_history`;
  - `autolead_retry_queue`;
  - `autolead_run_log`;
  - `autolead_app_log`;
  - `autolead_autofit_seen`;
  - `autolead_invite_history`;
  - `autolead_invite_message_state`.

## Гипотеза

Maintenance нужно сделать PostgreSQL-aware через фасад `utils.database`, не удаляя SQLite fallback. Для production env функции должны работать с PG-таблицами, для тестов и fallback — со старым SQLite backend.

## Проверка

- Добавлен `utils/runtime_store_pg_maintenance.py`.
- `clear_entire_database()` в `utils/database.py` теперь при включённых PG backend env вызывает PG-aware clear-функции:
  - `clear_leads`;
  - `clear_send_history`;
  - `clear_invite_history`;
  - `clear_retry_queue`;
  - `clear_run_log`;
  - `clear_app_log`;
  - `clear_autofit_seen`.
- `prune_old_data()` теперь при включённых PG backend env чистит PostgreSQL:
  - старые `autolead_run_log`;
  - старые `autolead_app_log`;
  - старые `autolead_autofit_seen`;
  - исчерпанные `autolead_retry_queue`.
- SQLite fallback сохранён.

## Наблюдение

Runtime-факты на сервере:

- `autolead_server_bot` — `healthy`;
- `traffichub_worker` — `healthy`;
- `/api/health` — `status=ok`;
- `prune_old_data(run_log_days=99999, autofit_seen_days=99999)` вернул:
  - `run_log: 0`;
  - `app_log: 0`;
  - `autofit_seen: 0`;
  - `retry_expired: 6`.
- После этого для `admin`:
  - `retry_pending`: `55`;
  - `get_leads_stats(days=30)` вернул `total_leads=789`, `total_sent=233`, `total_invited=0`, `retry_pending=55`.
- Unit suite:
  - `tests/test_database.py tests/test_retry_queue_matching.py` — `39 passed`.

## Вывод

Maintenance больше не является SQLite-only при production PostgreSQL env. SQLite остаётся fallback/test backend и schema compatibility layer.

Остаточный риск:

- `prune_old_data()` чистит expired retry независимо от выбранного большого срока логов. Это текущее ожидаемое поведение функции, но при smoke-проверках её нельзя считать полностью read-only.

## Следующий шаг

Зафиксировать финальное состояние миграции в архитектурной wiki: active Autolead runtime теперь PostgreSQL-backed, SQLite остаётся fallback/test/legacy compatibility, а не production source of truth.
