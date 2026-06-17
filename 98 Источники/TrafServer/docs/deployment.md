# Deployment

## Compose services

- `autolead_bot`
- `worker`
- `postgres`
- `redis`
- `license_auth`
- `license_server`
- `account_manager`
- `caddy`

Live-server health на 8 июня 2026 подтверждён для:

- `autolead_server_bot`
- `traffichub_worker`
- `traffichub_license_auth`
- `traffichub_license_server`
- `traffichub_account_manager`
- `traffichub_postgres`
- `traffichub_redis`
- `traffichub_caddy`

## Reverse proxy

`deploy/Caddyfile` публикует:

- `traffic-hubcrm.ru` -> `autolead_bot:8080`
- `auth.traffic-hubcrm.ru` -> `license_auth:8400`
- `license API` обслуживается `license_server:8401` как внутренний сервис server-side контура
- `am.traffic-hubcrm.ru` -> `account_manager:8000`
- `ai.traffic-hubcrm.ru` -> basic auth + AI perimeter root
- `am.traffic-hubcrm.ru/hermes` -> server-side Hermes Workspace UI behind AccountManager domain
- В текущем live-состоянии `/hermes/` обслуживает `hermes-fallback-dashboard.service` на `:3000`, потому что upstream `outsourc-e/hermes-workspace` Vite/TanStack Start зависал на `/hermes/*`.

Hermes Workspace на live работает как subpath-приложение под `/hermes/`, но часть его frontend/server routes использует absolute `/api/*`. Поэтому в `deploy/Caddyfile` для домена `am.traffic-hubcrm.ru` отдельно прокидываются:

- `/hermes*` -> `172.22.0.1:3000`
- root static assets `/assets*`, `/claude-*`, `/cover.*`, `/manifest.json`, `/sw.js` -> `/hermes{uri}` -> `172.22.0.1:3000`
- `/api/auth-check` -> `/hermes/api/auth-check`
- `/api/gateway-status` -> `/hermes/api/gateway-status`
- `/api/connection-status` -> `/hermes/api/connection-status`
- `/api/provider-usage` -> `/hermes/api/provider-usage`
- `/api/session-status` -> `/hermes/api/session-status`
- `/api/context-usage` -> `/hermes/api/context-usage`
- `/api/models` -> `/hermes/api/models`
- `/api/claude-proxy*` -> `/hermes/api/claude-proxy*`

Подтверждено runtime 17 июня 2026: `host.docker.internal:3000` внутри `traffichub_caddy` не является рабочим upstream для этого dev-сервера; используется `172.22.0.1:3000`.

Для client-side routing у Workspace под subpath также нужен ранний bootstrap `window.__HERMES_WORKSPACE_BASEPATH__ = '/hermes'`; иначе TanStack Router показывает внутреннюю 404-страницу при переходах `/hermes/chat/new` и `/hermes/chat/main`.

На 17 июня 2026 эта bootstrap-гипотеза не является активной live-правкой: основной публичный маршрут временно закрыт fallback dashboard. Fallback читает Obsidian vault `/home/codex/obsidian/hermes-victoria-vault` и проксирует chat completions в `victoria-recruiter-gateway.service`.

## Networks

После упрощения контейнерной схемы используются две основные сети:

- `core_net` — внутренняя связь `autolead_bot`, `worker`, `postgres`, `redis`, `license_auth`, `license_server`, `account_manager`
- `edge_net` — reverse-proxy и публичные upstream для `autolead_bot`, `license_auth`, `license_server`, `account_manager`, `caddy`

## Persistent storage

- `./data/runtime`
- `./data/runtime/secrets`
- `./data/logs`
- `./data/debug`
- `./data/backups`
- `./secrets`
- `./AccountManager/data`

Разделение по смыслу:

- `secrets/` — системные ключи установки: `.hwid`, `.salt_cache`, `traffic_hub_jwt_secret.key`, `license_*`
- `data/runtime/secrets/` — runtime-кэши приложения: `config.json`, `rabota_tokens.json`, `service_account.json`, `service_account__*.json`
- `data/runtime/` — `autolead.db`, `control.db`, `traffic_dashboard.db`, `autolead_access.json`, `worker.heartbeat`

Для локального `AccountManager` scaffold в workspace также ожидаются:

- `SESSION_SECRET_KEY`
- `ENCRYPTION_KEY` или `ACCOUNT_MANAGER_ENCRYPTION_KEY`

## Ключевые env

- `DATABASE_URL`
- `REDIS_URL`
- `DB_PATH`
- `CONTROL_DB_PATH`
- `RUNTIME_DATA_DIR`
- `RUNTIME_SECRETS_DIR`
- `CONFIG_FILE`
- `TOKEN_FILE`
- `GS_SERVICE_ACCOUNT_FILE`
- `SESSION_SECRET_KEY`
- `PUBLIC_BASE_URL`
- `AUTH_MODE`
- `EXTERNAL_AUTH_*`
- `LICENSE_AUTH_*`
- `ACCOUNT_MANAGER_*`

## Operational notes

- `autolead_bot` и `license_auth` слушают только loopback и публикуются наружу через Caddy.
- `license_server` также слушает loopback и не публикуется напрямую как публичный UI-сервис.
- `account_manager` дополнительно публикует websocket proxy на `1443`.
- `worker` теперь имеет heartbeat-файл и отдельный Docker healthcheck, а не просто long-running process.
- `worker` использует `secrets` только read-only; его runtime-кэши уже вынесены в `data/runtime/secrets`.
- Deployment всё ещё сильно зависит от `.env`, но после последнего этапа системные и runtime-secrets разведены лучше, чем раньше.
- `victoria-recruiter-gateway.service` слушает `127.0.0.1:8642` и отдаёт OpenAI-compatible endpoints для Hermes Workspace, используя тот же recruiter brain/vault, что и Telegram-bridge Виктории.
- `hermes-fallback-dashboard.service` слушает `0.0.0.0:3000` и является временным публичным UI для `/hermes/`, пока upstream Hermes Workspace debug не завершён.
