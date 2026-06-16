# 2026-06-17 API auth ws и frontend log bridge

## Симптом

- страницы `[[02_Архитектура/API]]` и `[[04_Код/Фронтенд]]` описывали контур слишком общо;
- не было короткой канонической фиксации по session cookie, websocket auth, AccountManager bridge и поведению live-лога.

## Зона системы

- web auth
- websocket log/status
- dashboard frontend
- AccountManager bridge

## Гипотеза

- legacy dashboard держится на session cookie `traffichub_session`, а websocket endpoints читают session principal из cookie scope;
- `AccountManager` открывается через bridge endpoint `/api/account-manager/token`, который только выпускает токен, но не делает role gating;
- dashboard `app.js` держит два websocket-канала: `/ws/log` и `/ws/status`;
- frontend отдельно обрабатывает `spinner`-сообщения и не должен смешивать их с обычной историей логов.

## Проверка

- просмотрен live source tree `/root/TrafficHub`:
  - `api/server.py`
  - `traffic_hub/api/routers/auth.py`
  - `dashboard/app.js`
- проверены точные участки:
  - session middleware
  - `/auth/session`, `/api/account-manager/token`
  - `/ws/log`, `/ws/status`
  - frontend token bootstrap и websocket reconnect/polling
  - frontend rendering `spinner`

## Наблюдение

- `api/server.py`:
  - `SessionMiddleware` ставится с `session_cookie="traffichub_session"`, `same_site="lax"`, `https_only` от `PUBLIC_BASE_URL`;
  - `/auth/session` и `/api/auth/session` читают `get_fresh_request_session_principal(request)`;
  - `/api/account-manager/token` требует authenticated session и возвращает bridge token через `_account_manager_access_token(...)`;
  - `/ws/log` и `/ws/status` закрывают соединение `1008`, если нет websocket session/token access;
  - `/ws/log` подключает snapshot последних логов через `ws_manager.recent_logs_for(..., limit=500)`;
  - `/ws/status` ведёт отдельный status stream.
- `traffic_hub/api/routers/auth.py`:
  - product API использует cookies `traffic_access_token`, `traffic_refresh_token`, `traffic_ws_token`;
  - `_set_traffic_auth_cookies(...)` пишет все три cookies как `httponly`, `samesite=lax`;
  - `/traffic-api/auth/bootstrap` умеет поднимать auth из existing cookies, refresh cookie или basic auth;
  - `/traffic-api/auth/me` читает токен из bearer header или cookies.
- `dashboard/app.js`:
  - `getAccountManagerAccessToken()` идёт в `/api/account-manager/token`;
  - `openAccountManagerApp()` и redirect-after-login подставляют token в `https://am.traffic-hubcrm.ru/`;
  - `connectLogWs()` открывает `/ws/log`, при разрыве включает fallback и reconnect;
  - `connectStatusWs()` открывает `/ws/status`, а при разрыве переключается на polling каждые `5` секунд;
  - `appendLog()` держит `spinner` как отдельную живую строку `.log-spinner`, а обычные сообщения дедуплицирует по `ts/level/text`.

## Вывод

- в системе есть два разных auth-контура:
  - legacy dashboard/session contour вокруг `api/server.py`
  - product API token/cookie contour вокруг `traffic_hub/api/routers/auth.py`
- `AccountManager` подключён через токен-мост из dashboard, а не через прямой shared session;
- log/status realtime надо отлаживать как два разных websocket-потока с разной деградацией:
  - `/ws/log` + history fallback
  - `/ws/status` + polling fallback

## Следующий шаг

- обновить `[[02_Архитектура/API]]`, `[[04_Код/Фронтенд]]` и при необходимости `[[02_Архитектура/Интеграции]]`;
- при следующих расследованиях auth/ws bug сначала определять, в каком контуре он живёт: session dashboard, product API cookies или external bridge.
