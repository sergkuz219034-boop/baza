# Architecture

## Кратко

Система состоит не из одного backend, а из нескольких связанных контуров:

- `Autolead runtime`
- `Autolead dashboard API`
- `TrafficHub worker`
- `TrafficHub API`
- `License Auth`
- `License Server`
- `AccountManager`
- `Caddy` как reverse proxy

Внутри текущего workspace для `AccountManager` отдельно восстановлен backend scaffold, потому что snapshot содержал только `api/main.py` без зависимых пакетов.

## Подтверждённые точки входа

- `services/leads_service.py` — основная runtime/business логика Autolead
- `remote_server_snapshot/traffic_hub/worker.py` — отдельный worker-процесс с heartbeat-health
- `remote_files/traffic_hub/app.py` — регистрация TrafficHub routers и websocket
- `AccountManager/api/main.py` — отдельный FastAPI сервис AccountManager
- `remote_server_snapshot/docker-compose.yml` — актуальная серверная схема контейнеров

Для `AccountManager` также подтверждены новые локальные модули:

- `remote_server_snapshot/AccountManager/database/*`
- `remote_server_snapshot/AccountManager/services/*`
- `remote_server_snapshot/AccountManager/api/routers/*`
- `remote_server_snapshot/AccountManager/dashboard/*`
- `remote_server_snapshot/AccountManager/chrome-extension/*`
- `remote_server_snapshot/AccountManager/scheduler.py`

## Ключевые data plane

- `autolead.db` — runtime leads/history/retry/run_log
- `control_*` в PostgreSQL — лицензии, per-user config, per-user auth, campaign history
- `control.db` — legacy snapshot/import source, не канонический runtime backend после миграции
- `traffic_dashboard.db` — SQLAlchemy БД TrafficHub
- `accounts.db` — отдельная БД AccountManager
- `app_log` в runtime SQLite — owner-scoped история логов UI
- `worker.heartbeat` — файл живости worker для Docker healthcheck

## Контейнерная схема

По текущему live compose сервисы такие:

- `autolead_bot`
- `worker`
- `postgres`
- `redis`
- `license_auth`
- `license_server`
- `account_manager`
- `caddy`

Сети после упрощения:

- `core_net` — внутренняя сервисная сеть
- `edge_net` — reverse-proxy и публичные upstream

Ключевая идея: отдельная `account_manager_net` удалена как лишняя. Связи `autolead_bot -> account_manager` и `caddy -> account_manager` покрываются двумя базовыми сетями без отдельного третьего слоя.

## Runtime storage layout

Runtime storage больше не монолитный:

- `data/runtime/` — SQLite/runtime-состояние
- `data/runtime/secrets/` — runtime-кэши пользователя и приложения
- `data/logs/` — прикладные логи
- `data/debug/` — debug-артефакты
- `data/backups/` — backup-артефакты
- `secrets/` — системные ключи и идентичность установки

Это важно, потому что раньше `secrets/` смешивал системные ключи и рабочие кэши. Сейчас runtime-secrets вынесены отдельно, а у `worker` системный `secrets` mount уже read-only.

## Ключевое архитектурное решение

Owner scoping проводится на уровне данных, а не только UI:

- в runtime таблицах через `owner_username`;
- в TrafficHub моделях через `owner_username`;
- в API через `scope_query(...)`, `get_owned_or_404(...)` и role checks;
- в тестах через `test_traffic_tenant_isolation.py`.

Это распространяется и на инфраструктурные данные:

- логи UI сохраняются owner-scoped;
- user-scoped Google service account файлы создаются отдельно (`service_account__<login>.json`);
- job queue и job status живут per-owner, а не в глобальной очереди исполнения.

## Ограничения

- Snapshot неполный.
- Часть роутеров видна только по импортам.
- Часть dashboard source отсутствует.
- README и часть wiki всё ещё содержат следы старой схемы `./data + ./secrets` и требуют дальнейшей синхронизации страница-за-страницей.

Детальная карта находится в wiki:

- `02 Архитектура/Architecture.md`
- `02 Архитектура/Backend.md`
- `02 Архитектура/Database.md`
