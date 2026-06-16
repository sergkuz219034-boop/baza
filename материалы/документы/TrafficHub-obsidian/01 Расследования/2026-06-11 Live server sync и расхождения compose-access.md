# 2026-06-11 Live server sync и расхождения compose-access

## Симптом

- Локальная wiki уже знала про `worker/postgres/redis`, но часть фактов держалась только на старом snapshot `2026-06-04` и partial compose bundle.
- Оставались сомнения по:
  - полноте `docker-compose.yml`;
  - реальному `control.backend`;
  - текущей auth/access модели Autolead;
  - актуальности `/traffic` и `/traffic-api`.

## Зона системы

- deployment/runtime;
- auth/authz;
- job queue / worker;
- embedded TrafficHub API.

## Гипотеза

- Live server уже ушёл дальше локального bundle:
  - compose полный;
  - `legacy_import_enabled=false` подтверждается health;
  - часть локальных замечаний про неподтверждённый `CONTROL_PG_LEGACY_IMPORT` устарела;
  - access-модель могла поменяться относительно старых ownership-описаний.

## Проверка

- SSH-доступ к `codex@150.241.70.31` подтверждён.
- На сервере `/root/TrafficHub`:
  - `git rev-parse HEAD` -> `b1c252e97fee58fcca1e5f04d1db0a60433b874b`
  - `git status --short` показывает dirty worktree, включая `README.md`, `CHANGELOG.md`, `docker-compose.yml`, `api/server.py`, `api/ws_manager.py`, `traffic_hub/worker.py`, `utils/control_store.py`, `wiki/*`.
- `docker ps` на `2026-06-11`:
  - `autolead_server_bot`
  - `traffichub_worker`
  - `traffichub_account_manager`
  - `traffichub_license_auth`
  - `traffichub_caddy`
  - `traffichub_license_server`
  - `traffichub_postgres`
  - `traffichub_redis`
- `curl http://127.0.0.1:8080/api/health` и `curl https://traffic-hubcrm.ru/api/health` возвращают:
  - `status=ok`
  - `version=1.2`
  - `app=TrafficHub`
  - `control.backend=postgres`
  - `control.legacy_import_enabled=false`
- `docker-compose.yml` на сервере подтверждает:
  - отдельные сервисы `worker`, `postgres`, `redis`;
  - `DATABASE_URL=${...postgresql+asyncpg://...@postgres:5432/traffichub}`
  - `REDIS_URL=${...redis://redis:6379/0}`
  - `CONTROL_DB_PATH=/app/data/runtime/control.db`
  - `CONTROL_PG_LEGACY_IMPORT=${...:-false}`
  - `CONTROL_LEGACY_SHEETS_FALLBACK=${...:-false}`
  - `CONTROL_LEGACY_SHEETS_DUAL_WRITE=${...:-false}`
  - `WORKER_HEARTBEAT_FILE=/app/data/runtime/worker.heartbeat`
  - сети `core_net` и `edge_net`
  - volumes `postgres_data`, `redis_data`, `caddy_data`, `caddy_config`
- `traffic_hub/worker.py` подтверждает:
  - start event bridge;
  - heartbeat file;
  - `claim_next_job(timeout=1)`;
  - single-active-thread loop внутри процесса worker.
- `traffic_hub/services/job_queue.py` подтверждает:
  - Redis keys `traffic_hub:jobs:queue`, `traffic_hub:jobs:state:<owner>`, `traffic_hub:jobs:active`, channel `traffic_hub:jobs:events`;
  - stale busy healing через `STALE_BUSY_AFTER = 6h`;
  - `request_stop_for_job()` публикует `job_stop_requested`;
  - memory fallback существует, если Redis недоступен.
- `traffic_hub/services/job_runner.py` подтверждает:
  - `VALID_COMMANDS = ("scrape", "upload", "send", "run", "automode", "superjob")`;
  - `redirect_stdout()` всё ещё активен;
  - cycle lock берётся через `leads_service.try_acquire_cycle_lock(owner)`.
- `api/authz.py` подтверждает:
  - browser session через `traffichub_session`;
  - HTTP fallback на Basic Auth при отсутствии session;
  - WebSocket access читает session principal, а не парсит Basic header/token.
- `api/autolead_access.py` подтверждает:
  - `get_autolead_access()` требует только `autolead_runtime_ready()` и наличие `principal.username`;
  - current code не сравнивает `principal.username` с configured owner;
  - `_FOREIGN_OWNER_MESSAGE` в файле есть, но в текущем кодовом пути не используется.
- `traffic_hub/app.py` и router definitions подтверждают mounted API prefixes:
  - `/traffic-api/auth`
  - `/traffic-api/leads`
  - `/traffic-api/offers`
  - `/traffic-api/finance`
  - `/traffic-api/messengers`
  - `/traffic-api/funnels`
  - `/traffic-api/click`
  - `/traffic-api/postbacks`
  - `/traffic-api/stats`
  - `/traffic-api/tools`
  - `/traffic-api/settings/integrations`

## Наблюдение

- До live sync локальный `artifacts/remote_sync/docker-compose.yml` был устаревшим и неполным относительно сервера.
- После расследования локальный compose snapshot переснят с live `docker-compose.yml`.
- `CONTROL_PG_LEGACY_IMPORT=false` теперь подтверждён live-кодом и env.
- `CONTROL_DB_PATH` уже `runtime/control.db`, а не старый `/app/data/control.db`.
- Модель `/traffic` как отдельной SPA устарела; рабочая модель — основной dashboard + embedded `/traffic-api/*`.
- Ключевой сдвиг в access-модели: Autolead runtime больше не owner-locked на уровне `get_autolead_access()`.

## Вывод

- Wiki можно снова опирать на live compose и live health, а не только на snapshot `2026-06-04`.
- Ownership нужно описывать аккуратно:
  - jobs/state/logs остаются owner-scoped;
  - но сам доступ к настроенному Autolead сейчас не режется по configured owner в `api/autolead_access.py`.
- Локальный evidence bundle полезен как offline reference, но не должен замещать live sync при наличии SSH.

## Следующий шаг

- Проверить route-level ограничения внутри `traffic_hub/api/routers/*`, чтобы отделить общий auth-gate от per-endpoint RBAC.
- Перепроверить, intentional ли снятие owner-lock в `api/autolead_access.py`, или это регрессия доступа.
