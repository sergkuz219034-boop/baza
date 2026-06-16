# 2026-06-17 P1 boundary active runtime fallback

## Симптом

После общей классификации remaining SQLite surface оставался практический вопрос:

- какие P1-модули ещё реально сидят рядом с active runtime contract;
- что в них можно считать кандидатом на вынос из production-adjacent path;
- что пока рано убирать без отдельного cleanup stream.

## Зона системы

- live repo `/root/TrafficHub`
- `docker-compose.yml`
- `utils/database.py`
- `utils/runtime_store_schema.py`
- `utils/runtime_store_maintenance.py`

## Гипотеза

Главный production-adjacent риск в P1 не в том, что SQLite fallback просто существует, а в том, что:

1. `utils/database.py` по-прежнему выглядит как dual-path facade почти для всех runtime операций;
2. `init_db()` безусловно вызывает SQLite schema/bootstrap path;
3. SQLite cleanup path всё ещё лежит рядом с PostgreSQL-aware maintenance и не отрезан от mental model production runtime.

## Проверка

По live-коду подтверждено:

- `docker-compose.yml` поднимает runtime c:
  - `AUTOLEAD_RUNTIME_LOGS_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_DELIVERY_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_LEADS_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_AUTOFIT_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_INVITES_BACKEND=postgres`
  - `AUTOLEAD_RUNTIME_CONTROL_SYNC_BACKEND=postgres`
- `utils/database.py:init_db()` сначала вызывает `utils.runtime_store_schema.init_db(...)`, а уже потом инициализирует PostgreSQL backends;
- `utils/database.py` имеет PostgreSQL ветки почти для всех runtime операций, но оставляет SQLite fallback как default path при выключенных env;
- `utils/database.py:clear_entire_database()` и `utils/database.py:prune_old_data()` уже умеют PostgreSQL branch, но SQLite fallback остаётся рядом;
- `utils/runtime_store_schema.py` создаёт и мигрирует полный набор SQLite runtime-таблиц:
  - `leads`
  - `send_history`
  - `invite_history`
  - `invite_message_state`
  - `retry_queue`
  - `run_log`
  - `app_log`
  - `autofit_seen`
  - `control_sync_queue`
- `utils/runtime_store_maintenance.py` обслуживает SQLite-only cleanup через `DELETE`, `VACUUM`, `wal_checkpoint`.

## Наблюдение

### `utils/database.py`

Что keep сейчас:

- PostgreSQL routing branches как production contract;
- facade boundary, потому что через него идёт активный runtime call-path;
- fallback до тех пор, пока cleanup явно не вынесет SQLite runtime support в отдельный слой.

Что candidate for cleanup:

- сделать branch boundary явнее;
- перестать воспринимать SQLite fallback как равноправный production path;
- после отдельного cleanup можно выносить SQLite runtime support из главного facade или жёстко изолировать его.

### `utils/runtime_store_schema.py`

Что keep сейчас:

- legacy/bootstrap совместимость, если проект ещё должен уметь поднимать SQLite runtime storage в локальном/старом сценарии.

Что candidate for cleanup:

- безусловный вызов из `utils/database.py:init_db()`;
- production-adjacent позиционирование;
- полный SQLite schema bootstrap при уже подтверждённом PostgreSQL-first live runtime.

Это выглядит как самый сильный кандидат на отделение от active runtime contract.

### `utils/runtime_store_maintenance.py`

Что keep сейчас:

- SQLite cleanup logic, если SQLite runtime fallback официально ещё поддерживается.

Что candidate for cleanup:

- использование как подразумеваемого соседа production maintenance path;
- отсутствие явной границы между `runtime_store_pg_maintenance.py` и legacy SQLite cleanup role.

Production путь уже должен читаться через PostgreSQL-aware maintenance как основной.

## Вывод

Для P1-модулей boundary на `2026-06-17` выглядит так:

- `utils/database.py` пока нельзя просто удалять или радикально упрощать без cleanup stream, но его надо описывать как PostgreSQL-first facade с legacy fallback;
- `utils/runtime_store_schema.py` — главный кандидат на вынос из active runtime init-path;
- `utils/runtime_store_maintenance.py` — кандидат на перевод в явно legacy/fallback слой рядом с PostgreSQL maintenance;
- если цель — уменьшить ложную диагностику, first target не удаление всех SQLite модулей, а разрыв production mental model с безусловным SQLite init/bootstrap.

## Следующий шаг

1. Поднять это boundary в краткий канон и техдолг.
2. Отдельно зафиксировать, что `init_db()` touching SQLite schema при PostgreSQL-first runtime — главный confusing factor.
3. После этого можно планировать уже инженерный cleanup stream по коду, а не только по документации.
