# 2026-06-17 Remaining SQLite surface после PostgreSQL-first runtime

## Симптом

После фиксации шагов 1–8 миграции root-канон всё ещё создавал впечатление, что active runtime migration не завершена и впереди перенос `autofit_seen`, `invite_history` и `control_sync_queue`.

Нужно было отделить:

- что уже реально migrated в live runtime;
- что ещё живёт в SQLite только как fallback/test/schema compatibility;
- что относится не к Autolead runtime, а к другим legacy/store контурам.

## Зона системы

- live repo `/root/TrafficHub`
- `docker-compose.yml`
- `utils/database.py`
- `utils/runtime_store_schema.py`
- `utils/runtime_store_maintenance.py`
- `utils/runtime_repository.py`
- `tests/test_database.py`
- `services/stats_service.py`
- `utils/control_store.py`

## Гипотеза

На `2026-06-17` active Autolead runtime уже PostgreSQL-first, а remaining SQLite surface локализуется в четырёх типах мест:

1. SQLite fallback внутри фасада `utils.database.py`
2. schema init и legacy compatibility в `utils/runtime_store_schema.py`
3. maintenance fallback в `utils/runtime_store_maintenance.py`
4. test/local-only paths и отдельный `control_store` контур

## Проверка

Live SSH check против `/root/TrafficHub` подтвердил:

- `HEAD = a8f0be2`
- контейнеры `autolead_server_bot`, `traffichub_worker`, `traffichub_postgres` healthy
- в `docker-compose.yml` по умолчанию включены:
  - `AUTOLEAD_RUNTIME_LOGS_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_DELIVERY_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_LEADS_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_AUTOFIT_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_INVITES_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_CONTROL_SYNC_BACKEND=postgres`

В live-коде подтверждено наличие PostgreSQL backend-модулей:

- `utils/runtime_store_pg_logs.py`
- `utils/runtime_store_pg_delivery.py`
- `utils/runtime_store_pg_leads.py`
- `utils/runtime_store_pg_autofit.py`
- `utils/runtime_store_pg_invites.py`
- `utils/runtime_store_pg_control_sync.py`
- `utils/runtime_store_pg_maintenance.py`

Дополнительно проверено:

- `utils/database.py` уже маршрутизирует active runtime operations в PostgreSQL backends при включённых env;
- `clear_entire_database()` и `prune_old_data()` уже имеют PostgreSQL-aware ветку;
- `utils/runtime_repository.py` для owner leads/history/summary умеет читать PostgreSQL при `AUTOLEAD_RUNTIME_LEADS_BACKEND=postgres`;
- `tests/test_database.py` остаётся SQLite-oriented test suite;
- `utils/runtime_store_schema.py` остаётся SQLite schema/bootstrap слоем;
- `utils/control_store.py` живёт в отдельном `control.db`/hybrid contour и не равен active Autolead runtime migration.

## Наблюдение

Active PostgreSQL-first runtime уже покрывает:

- `autolead_app_log`
- `autolead_run_log`
- `autolead_send_history`
- `autolead_retry_queue`
- `autolead_leads`
- `autolead_autofit_seen`
- `autolead_invite_history`
- `autolead_invite_message_state`
- `autolead_control_sync_queue`

Remaining SQLite surface по факту:

### 1. Fallback/runtime compatibility

- fallback-ветки `utils/database.py`
- SQLite backend-модули `utils/runtime_store_*.py`

### 2. Schema compatibility

- `utils/runtime_store_schema.py` продолжает создавать `leads`, `send_history`, `invite_history`, `invite_message_state`, `retry_queue`, `run_log`, `app_log`, `autofit_seen`, `control_sync_queue`

### 3. Maintenance fallback

- `utils/runtime_store_maintenance.py` остаётся SQLite-only fallback модулем
- production path уже routed в `utils/runtime_store_pg_maintenance.py`

### 4. Test/local-only paths

- `tests/test_database.py` проверяет SQLite fixture path
- `tests/test_leads_router.py` использует прямой SQLite connect
- `services/stats_service.py` остаётся завязан на SQLite path только для части postback-метрик из `traffic_hub` БД

### 5. Hybrid read/metrics path

- `utils/runtime_repository.py` уже умеет PostgreSQL read path для owner leads/history/summary
- но сам модуль всё ещё содержит SQLite branch как read fallback
- это не отдельная незавершённая миграция таблиц, а ещё не вычищенная dual-path реализация

### 6. Отдельный legacy/control contour

- `utils/control_store.py` использует `control.db` и hybrid control-store path
- `CONTROL_PG_LEGACY_IMPORT` управляет legacy import behaviour
- это отдельная зона и не должна смешиваться с active Autolead runtime migration

## Вывод

На `2026-06-17` migration status надо описывать так:

- active Autolead runtime migration в PostgreSQL по существу завершена;
- SQLite больше не является production source of truth для основного runtime path;
- remaining SQLite surface — это fallback/test/schema/legacy compatibility, а не незавершённый перенос основных runtime-таблиц.

## Следующий шаг

Следующий инженерный этап уже не “мигрировать ещё одну runtime-таблицу”, а:

1. классифицировать каждый remaining SQLite path как:
   - production fallback
   - test-only
   - hybrid read/metrics path
   - schema compatibility
   - legacy contour
2. решить, какие из них можно удалить из active runtime contract;
3. отдельно задокументировать границу между Autolead runtime migration и `control_store` migration.
