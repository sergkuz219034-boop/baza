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

- [[04_План/Материалы/сырьё/документы/TrafficHub-obsidian/01 Расследования/2026-06-17 API auth ws и frontend log bridge]]

## Дальше

- [[02_Код/Код/Бэкенд|Бэкенд]]
- [[02_Код/Код/Фронтенд|Фронтенд]]
- [[04_План/Материалы/сырьё/документы/TrafficHub-obsidian/03-API|Архивный API-слой]]

## 2026-10-12 — local JWT sessions и tenant context (source, до deploy)

Server commit `1c7a491e4dbabc280e6b27b7f56fe0ca4c7ef109` разделяет local JWT
access/refresh через purpose, sid/jti и Redis-backed sessions. Refresh jti
ротируется CAS; повтор401, logout отзывает session обоих token types,
store outage503 fail-closed. Legacy typeless local JWT требует повторного входа
после публикации. External/license authentication paths сохранены.
Источник: `/root/TrafficHub/traffic_hub/services/local_auth_sessions.py`,
`traffic_hub/api/routers/auth.py`, `traffic_hub/api/deps.py`.

Membership query использует существующую сортировку personal desc/id asc с
limit1, сохраняя membership restriction; несколько memberships не приводят
к scalar_one_or_none500. Выбор чужого tenant не разрешён.

Проверки source:12 auth тестов с настоящим isolated Redis refresh CAS и29
связанных role/embedded/tenant tests PASS. Deploy этой записи **не подтверждён**:
основной release выполняется отдельно. Доказательства и границы:
`C:/Users/admin/Desktop/Project/outputs/medium-server-fixes-20261012/auth/REPORT.md`,
`integration.txt`, `related-tests.txt`, `commit.txt`.
