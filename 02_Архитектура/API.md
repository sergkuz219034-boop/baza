# API

## Подтверждено

- legacy web/API слой живёт в `api/server.py`
- embedded `traffic-api` слой живёт в `traffic_hub/app.py`
- legacy dashboard session-контур использует `SessionMiddleware` с cookie `traffichub_session`
- websocket endpoints подтверждены:
  - `/ws/log`
  - `/ws/status`
- embedded traffic websocket подтверждён отдельно:
  - `/traffic-ws`
  - `/ws` внутри `traffic_hub/app.py`
- health endpoint:
  - `/api/health`

## Что важно

- auth-модель гибридная: session cookie + fallback API auth;
- роли legacy dashboard подтверждены по коду 2026-07-10: `operator`, `user`, `admin`;
- `operator` — минимальная рабочая роль: может открыть owner-scoped экран лидов, но не должен запускать Autolead jobs, менять настройки, офферы, техработы, system actions, TrafficHub CRM или AccountManager;
- `user` — обычная рабочая роль с доступом к Autolead настройкам/офферам/jobs в рамках своего owner-context;
- `admin` — административная роль, включая управление аккаунтами, aliases, maintenance и системные действия;
- `/api/account-manager/token` является bridge endpoint, а не конечной точкой role gating;
- `/ws/log` и `/ws/status` авторизуются через websocket session/token access и закрываются `1008`, если principal/access не прошёл проверку;
- `/ws/log` отдаёт snapshot последних owner-scoped логов при подключении;
- `/ws/status` — отдельный realtime-канал статусов задач, не тот же поток, что live-log;
- API нельзя рассматривать без owner/runtime semantics.

## Product API auth contour

- `traffic_hub/api/routers/auth.py` живёт отдельным cookie/token контуром;
- cookies:
  - `traffic_access_token`
  - `traffic_refresh_token`
  - `traffic_ws_token`
- `/traffic-api/auth/bootstrap` умеет поднимать auth из existing cookies, refresh cookie или basic auth;
- `/traffic-api/auth/me` читает bearer token или product auth cookies;
- это не тот же механизм, что session cookie `traffichub_session` в legacy dashboard.

## AccountManager bridge

- `dashboard/app.js` получает token через `/api/account-manager/token`;
- затем открывает `https://am.traffic-hubcrm.ru/` с query param `token=...`;
- значит, баги входа в `AccountManager` надо локализовать отдельно от общей session-аутентификации dashboard.

## Расследование

- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-17 API auth ws и frontend log bridge]]

## Дальше

- [[04_Код/Бэкенд|Бэкенд]]
- [[04_Код/Фронтенд|Фронтенд]]
- [[материалы/документы/TrafficHub-obsidian/03-API|Архивный API-слой]]
