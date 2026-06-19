# БАГ-004: admin не входил в TrafficHub CRM

## Симптом

UI `/login` показывал `Неверный логин или пароль` для пользователя `admin`.

## Зона системы

- `api/server.py` — legacy session endpoints `/auth/login`, `/auth/session`, `/api/auth/login`.
- `traffic_hub/api/routers/auth.py` — JWT/cookie endpoints `/traffic-api/auth/login`, `/traffic-api/auth/me`.
- PostgreSQL таблицы `users`, `control_license_users`.
- `utils.license.validate_user()` — проверка bcrypt hash в PostgreSQL-режиме.

## Гипотеза

Отказ связан не с frontend, а с auth data: `admin` существует, но сохранённый bcrypt hash не соответствует текущему паролю. Дополнительно cookie-flow `/traffic-api/auth/me` может падать до чтения cookies из-за `OAuth2PasswordBearer(auto_error=True)`.

## Проверка

- В PostgreSQL `users` есть `admin`, `role=admin`, `is_active=true`, bcrypt hash присутствует.
- В `control_license_users` есть `admin`, `role=admin`, `active=true`, bcrypt hash присутствует.
- До исправления `utils.license.validate_user("admin", ...)` возвращал `False`.
- Все login endpoints до исправления возвращали `401`.
- После reset hash:
  - `/auth/login` -> `200`;
  - `/auth/session` -> `200`;
  - `/traffic-api/auth/login` -> `200`;
  - `/traffic-api/auth/me` с cookies -> `200`;
  - `autolead_access.allowed=true`, `owner_username=admin`.

## Наблюдение

`/traffic-api/auth/me` использовал `OAuth2PasswordBearer` без `auto_error=False`. Поэтому запрос без `Authorization` мог завершаться `401` до того, как handler проверял `traffic_access_token` / `traffic_ws_token` cookies.

## Вывод

Причина была двойная:

- live auth hash для `admin` не соответствовал текущему паролю;
- JWT/cookie endpoint `/traffic-api/auth/me` не был корректен для cookie-only flow.

## Решение

- Обновлены bcrypt hashes для `admin` в `users.hashed_password` и `control_license_users.secret_salt`.
- В `traffic_hub/api/routers/auth.py` `OAuth2PasswordBearer` переключён на `auto_error=False`.
- В `tests/test_traffic_auth_external.py` добавлена проверка `/traffic-api/auth/me` после local cookie login.

## Следующий шаг

Если пароль `admin` меняется через UI, проверять оба сценария:

- legacy session flow: `/auth/login` + `/auth/session`;
- JWT/cookie flow: `/traffic-api/auth/login` + `/traffic-api/auth/me`.
