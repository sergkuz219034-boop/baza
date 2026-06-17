# API

## Обзор

В текущем состоянии система состоит из нескольких API-контуров:

- `Dashboard / operational API` — управление Autolead runtime, settings, jobs, leads, debug и system-операциями
- `TrafficHub API` — отдельный `/traffic-api/*` контур для CRM/офферов/лидов/интеграций/статистики
- `License Auth` — внешний auth-контур для bearer/JWT входа
- `License Server` — серверная license API
- `AccountManager API` — отдельный admin-only сервис

Ниже перечислено только то, что подтверждено кодом и/или live-сервером.

## Dashboard / operational API

Основные группы маршрутов:

- `/api/jobs/*`
- `/api/leads/*`
- `/api/stats/*`
- `/api/settings/*`
- `/api/offers/*`
- `/api/system/*`
- `/api/debug/*`
- `/api/avito/*`
- `/api/control/*`
- `/api/logs`
- `/api/health`

### Jobs

Подтверждены:

- `GET /api/jobs/status`
- `POST /api/jobs/run`
- `POST /api/jobs/stop`

Текущая модель отличается от старой общей очереди:

- очередь owner-scoped;
- один пользователь не блокирует другого;
- для каждого owner хранится отдельный state;
- источник хранения очереди — Redis, при недоступности есть in-memory fallback;
- worker читает очередь отдельно от web-контейнера.

Поддерживаемые команды:

- `scrape`
- `upload`
- `send`
- `run`
- `automode`
- `superjob`

### Логи и статус

Подтверждены:

- `GET /api/logs`
- `WS /ws/log`
- `WS /ws/status`
- `GET /api/health`

Фактическая модель:

- UI-логи сохраняются в `app_log` с `owner_username`;
- `/api/logs` для `user` читает owner-scoped persistent `app_log` и дополняет его live `ws_manager`-сообщениями;
- `DELETE /api/logs` очищает и persistent `app_log`, и live in-memory cache;
- `/ws/log` стримит owner-scoped сообщения;
- `/ws/status` стримит owner-scoped статус текущего job;
- worker дополнительно пишет heartbeat-файл `worker.heartbeat`, который используется Docker healthcheck, но не является отдельным публичным API.

### Settings

Подтверждены:

- `GET /api/settings`
- `PATCH /api/settings`
- `GET /api/settings/operator`
- `PATCH /api/settings/operator`
- `GET /api/settings/session`
- `GET /api/settings/superjob`
- `PATCH /api/settings/superjob`
- `GET /api/settings/export`
- `POST /api/settings/import`
- `POST /api/settings/upload-sa`
- `GET /api/settings/rabota-auth-url`
- `POST /api/settings/rabota-token`
- `DELETE /api/settings/db`
- `DELETE /api/settings/db/autofit`
- `DELETE /api/settings/db/leads`
- `DELETE /api/settings/db/send-history`
- `DELETE /api/settings/db/invite-history`
- `DELETE /api/settings/db/screenshots`
- `DELETE /api/settings/db/retry-queue`
- `DELETE /api/settings/db/run-log`

Важно:

- runtime config теперь живёт в `data/runtime/secrets/config.json`;
- Rabota tokens — в `data/runtime/secrets/rabota_tokens.json`;
- service account cache — в `data/runtime/secrets/service_account.json` и `service_account__<login>.json`;
- код поддерживает совместимость со старыми относительными значениями вроде `secrets/service_account.json`, но канонический путь уже новый.

### Leads / Stats / Debug

Подтверждены:

- `GET /api/leads`
- `GET /api/leads/export`
- `POST /api/leads/{id}/resend`
- `GET /api/stats/summary`
- `GET /api/stats/history`
- `GET /api/debug/stats`
- `GET /api/debug/recent`
- `GET /api/debug/run-log`

Owner-scoping подтверждён кодом:

- выборки по лидам ограничены текущим `owner_username`;
- resend и export работают только в пределах данных владельца;
- debug-эндпоинты не должны видеть чужие runtime-записи.

### System / Control

Подтверждены:

- `GET /api/system/health`
- `GET /api/system/git-status`
- `POST /api/system/update-from-git`
- `GET /api/system/environment`
- `GET /api/system/backups`
- `POST /api/system/backups`
- `DELETE /api/system/backups/{name}`
- `GET /api/control/health`
- `POST /api/control/sync-now`
- `POST /api/control/import-legacy-sheets`

## TrafficHub API

Подтверждён отдельный встроенный контур `/traffic-api/*`.

Явно подтверждены роутеры:

- `/traffic-api/settings/integrations`
- `/traffic-api/leads`
- `/traffic-api/offers`
- `/traffic-api/postbacks`
- `/traffic-api/stats`

По импортам также ожидаются:

- `auth`
- `finance`
- `funnels`
- `messengers`
- `tracking`
- `tools`

### TrafficHub ownership model

Подтверждено по коду:

- используются `owner_username` и `tenant_id`;
- есть helpers `scope_query(...)`, `get_owned_or_404(...)`, `owner_username_for(...)`;
- часть сущностей дополнительно ужесточена tenant hardening миграциями.

То есть в TrafficHub multi-tenant и owner-scope реализованы не только на UI-уровне, а на уровне запросов и моделей.

## Authentication / Authorization

### Dashboard

Dashboard использует:

- сессионную авторизацию;
- HTTP Basic compatibility;
- role-модель `user` / `admin`.

Для большинства operational endpoints применяются:

- `require_authenticated`
- `require_operator`
- `require_admin`
- дополнительные Autolead access checks через `get_autolead_access(...)`.

### TrafficHub

TrafficHub поддерживает:

- session / cookie flow;
- HTTP Basic compatibility;
- локальный JWT;
- внешний bearer/JWT сценарий через `license_auth`.

### AccountManager

`AccountManager` — отдельный сервис со своим `SESSION_SECRET_KEY` и отдельной admin-only моделью доступа.

## License Auth

Подтверждено:

- `GET /health`
- `GET /login`
- `POST /login`
- `POST /token`

Назначение:

- проверка пользователя;
- выпуск access token;
- redirect back в публичный UI.

## License Server

Подтверждено по compose и коду:

- отдельный контейнер `license_server`
- отдельный health endpoint
- использование `license_private_key.xml` и `license_public_key.xml`

Это server-side контур лицензирования, не основной пользовательский UI.

## AccountManager API

В текущем workspace подтверждены:

- `/api/telegram/connect`
- `/api/telegram/confirm`
- `/api/telegram/import-session`
- `/api/telegram/accounts/*`
- `/api/google/import`
- `/api/google/accounts/*`
- `/api/google/refresh-pending`
- `/api/social/connect`
- `/api/social/accounts/*`
- `/api/proxies/*`
- `/api/dashboard/summary`
- `/api/accounts`

Важно:

- Google import/check реализован как рабочий backend flow;
- Telegram и social OAuth поддерживают live-path при наличии зависимостей и окружения;
- при неполной среде AccountManager уходит в fallback mode, а не молча ломается.

## Что изменилось относительно старой схемы

- больше нет общей очереди “на всех пользователей”;
- логи больше не должны смешиваться между пользователями;
- runtime-secrets вынесены из системного `secrets/` в `data/runtime/secrets/`;
- worker теперь отдельный контейнер с heartbeat-healthcheck;
- часть старых страниц и заметок ещё может ссылаться на `secrets/config.json`, но это уже legacy-форма, а не канон.
