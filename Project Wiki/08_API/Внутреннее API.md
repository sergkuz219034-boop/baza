# Внутреннее API

## Подтверждённое

- web/API обслуживается `autolead_server_bot`;
- internal router map монтируется через `traffic_hub/app.py`;
- websocket endpoints: `/ws/log`, `/ws/status`.

## Auth/session endpoints

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/session`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`
- `GET /api/auth/me`

## Router families

- `/api/leads`
- `/api/jobs`
- `/api/stats`
- `/api/settings`
- `/api/offers`
- `/api/system`
- `/api/debug`
- `/api/avito`
- `/api/control`

## Access contract

- browser session опирается на cookie `traffichub_session`;
- basic auth fallback допустим для HTTP-path без session;
- websocket path (`/ws/log`, `/ws/status`) требует session principal и не является полноценным Basic-auth контуром;
- helper `check_ws_basic_token()` исторически назван неудачно: фактически он не даёт отдельного token-auth для websocket.

## Account Manager bridge

- `GET /api/account-manager/token` доступен аутентифицированному пользователю;
- bridge выдаёт HS256 JWT с `sub`, `username`, `role`, `iat`, `exp`;
- окончательные role restrictions остаются внутри самого Account Manager.

## Источник

- [[01 Проекты/ТрафикХаб/Контур проекта]]
- [[01 Проекты/ТрафикХаб/Точки входа]]

## Полный API-архив

- [[Project Wiki/raw/docs/TrafficHub-obsidian/03-API/Overview|Legacy API overview]]
- [[Project Wiki/raw/docs/TrafficHub-obsidian/03-API/Endpoints|Legacy API endpoints]]
- [[Project Wiki/raw/docs/TrafficHub-obsidian/03-API/Auth|Legacy API auth]]
- [[Project Wiki/raw/docs/TrafficHub-obsidian/03-API/WebSocket|Legacy API websocket]]
