# 2026-06-07 registration only wrote to control store

## Симптом

Пользователь успешно проходил регистрацию по activation key, но затем не мог войти в TrafficHub. UI показывал `Неверный логин или пароль`.

## Проверка

1. `validate_user("Artemka", "1881")` на сервере возвращал `False`.
2. В `control.db` пользователь `Artemka` существовал:
   - логин записан,
   - bcrypt-хэш пароля есть,
   - роль `user`.
3. В Postgres `users` записи `Artemka` не было.
4. `utils/license.py` показал, что при production `DATABASE_URL` авторизация идёт через Postgres.
5. `api/server.py::_apply_activate_license_key()` записывал пользователя только в `control_store`.

## Вывод

Регистрация писала только в legacy/local store, а runtime логин проверял только primary Postgres auth source. Из-за этого регистрация выглядела успешной, но вход ломался.

## Что исправлено

- В `api/server.py::_apply_activate_license_key()` добавлена синхронизация пользователя в Postgres:
  - если пользователя нет, он создаётся;
  - если есть, ему обновляются пароль, активность и роль.
- После фикса `Artemka` был дозаписан в Postgres вручную из существующей записи `control.db`.

## Результат

- `validate_user("Artemka", "1881") == True`
- дальнейшие регистрации через activation flow должны сразу создавать рабочий логин для production auth.
