# API

Теги: #архитектура

## Dashboard API

Подтверждены группы endpoint:

- `jobs`: `/api/jobs/status`, `/api/jobs/run`, `/api/jobs/stop`
- `settings`: чтение, patch, import/export, session, SuperJob, vacancy aliases
- `license accounts`: list, role patch, update, delete
- `db cleanup`: `DELETE /api/settings/db/*`
- `rabota auth`: auth URL и token exchange
- `logs/status`: `/api/logs`, `WS /ws/log`, `WS /ws/status`
- `health/system/control`: `/api/health`, `/api/system/*`, `/api/control/*`

## Что важно сейчас

- job queue owner-scoped, а не общая на всех пользователей;
- worker исполняет очереди отдельно от web-процесса;
- логи UI сохраняются owner-scoped в `app_log`;
- часть runtime access logic завязана на `AutoleadAccess`, который проверяет наличие runtime-secrets и конфигурации для пользователя.

## TrafficHub API

Подтверждённые router prefixes:

- `/traffic-api/settings/integrations`
- `/traffic-api/leads`
- `/traffic-api/offers`
- `/traffic-api/postbacks`
- `/traffic-api/stats`

Подтверждённые TrafficHub websocket endpoints:

- `/traffic-ws`
- `/ws`

Подтверждённая ownership-модель:

- `owner_username`
- `tenant_id`
- query scoping через ownership helpers
- отдельные tenant hardening миграции

## API gaps

По `traffic_hub/app.py` должны существовать дополнительные роутеры, но их исходники отсутствуют в workspace:

- `auth`
- `finance`
- `funnels`
- `messengers`
- `tracking`
- `tools`

Поэтому полный public contract проекта в этом workspace не восстановим на 100%.

## AccountManager account modules

В локальном snapshot теперь присутствуют:

- `Telegram`: connect, confirm, import-session, list/detail/delete/status/reconnect
- `Google`: import, list/detail/delete/check/refresh
- `Social`: connect, list/detail/delete/check/reauth
- `Proxies`: list/create/update/delete

Ограничение:

- live Telethon и Playwright сценарии пока scaffold-only, но API и persistence contract уже собраны.

## Runtime-path note

Канонические runtime-secrets после актуальной серверной схемы:

- `data/runtime/secrets/config.json`
- `data/runtime/secrets/rabota_tokens.json`
- `data/runtime/secrets/service_account.json`

Старые относительные значения вида `secrets/service_account.json` поддерживаются кодом как compatibility layer, но больше не являются каноническим storage layout.

## Смежные страницы

- [[Authentication]]
- [[Authorization]]
- [[Integrations]]
