# Auth и Access

## Источник

- live code `api/authz.py`
- live code `api/autolead_access.py`
- live code `api/server.py`
- live code `config/settings.py`
- расследование [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-11 Live server sync и расхождения compose-access]]

## Аутентификация

- Browser path:
  - `POST /auth/login`
  - `POST /auth/logout`
  - `GET /auth/session`
- Compatibility path:
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
  - `GET /api/auth/session`
  - `GET /api/auth/me`
- Session cookie:
  - имя `traffichub_session`
  - создаётся через `SessionMiddleware`
- HTTP fallback:
  - если session нет, `authenticate_basic_credentials()` принимает HTTP Basic и валидирует пользователя через `utils.license.validate_user()`

## Авторизация

- Principal:
  - `username`
  - `role`
- Роль резолвится через `utils.access.resolve_user_role()`.
- Базовые guard-ы:
  - `require_authenticated`
  - `require_operator`
  - `require_admin`
- `api/server.py` вешает `authenticate_basic_credentials` на router-ы:
  - `/api/leads`
  - `/api/jobs`
  - `/api/stats`
  - `/api/settings`
  - `/api/offers`
  - `/api/system`
  - `/api/debug`
  - `/api/avito`
  - `/api/control`

## WebSocket access

- Точки:
  - `/ws/log`
  - `/ws/status`
- WebSocket не парсит Basic header/token.
- `check_ws_basic_token()` фактически лишь проверяет наличие session principal в websocket scope.
- Следствие:
  - browser session обязательна для websocket;
  - “basic token” в названии helper-а исторический misnomer.

## Autolead access gate

- Runtime readiness считается через `autolead_runtime_ready()`.
- Если runtime не готов:
  - доступ запрещён;
  - сообщение: `Сначала загрузите secrets / импортируйте настройки.`
- Если principal отсутствует:
  - доступ запрещён.
- Если principal есть и runtime готов:
  - `get_autolead_access()` сейчас возвращает `allowed=True`.

## Что важно про ownership

- В `api/autolead_access.py` есть понятия:
  - `owner_username`
  - `autolead_access.json`
  - `autolead_owner_username` в runtime `config.json`
- Но current access gate не сравнивает `principal.username` с configured owner.
- `_FOREIGN_OWNER_MESSAGE = "Этот Autolead настроен для другого пользователя."` в коде есть, но в текущем кодовом пути не используется.
- Следствие:
  - owner-scoped runtime state и secrets существуют;
  - но запрет “чужому пользователю нельзя заходить в настроенный Autolead” на уровне `get_autolead_access()` сейчас не enforced.

## Runtime paths

- `RUNTIME_SECRETS_DIR = /app/data/runtime/secrets`
- `AUTOLEAD_ACCESS_FILE = /app/data/runtime/autolead_access.json`
- `CONFIG_FILE = /app/data/runtime/secrets/config.json`
- `TOKEN_FILE = /app/data/runtime/secrets/rabota_tokens.json`

## Account Manager bridge

- `GET /api/account-manager/token` доступен любому аутентифицированному пользователю TrafficHub.
- Endpoint выдаёт HS256 JWT с:
  - `sub`
  - `username`
  - `role`
  - `iat`
  - `exp`
- Ограничение по ролям остаётся внутри самого Account Manager, а не на входном мостике.

## Риск

- Старые заметки, где WebSocket описан как Basic-auth контур, устарели.
- Старые заметки, где Autolead жёстко owner-locked на access-слое, тоже устарели или требуют отдельной проверки намерения.
