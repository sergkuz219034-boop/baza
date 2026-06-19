# БАГ-013 Artem не входит после перезаписи пароля

## Симптом

Пользователь `Artem` видит `Неверный логин или пароль` на login screen, хотя вводит выданный пароль.

## Зона системы

- `utils/license.py`
- `api/routers/settings_license_accounts.py`
- PostgreSQL `users.hashed_password`
- PostgreSQL `control_license_users.secret_salt`
- dashboard admin panel `license-accounts`

## Гипотеза

Auth сломан не из-за cookie/session и не из-за рассинхронизации `users` vs `control_license_users`, а из-за того, что оба auth-хранилища были перехешированы от неправильного значения.

## Проверка

Live runtime script внутри `/app` проверил:

- `validate_user("Artem", <текущий пароль>) -> false`;
- `users.hashed_password` присутствует;
- `control_license_users.secret_salt` присутствует;
- bcrypt-check указанного пароля против обоих hash -> false;
- `get_user_role("Artem") -> user`.

## Наблюдение

Обе таблицы были синхронны между собой, но обе не соответствовали текущему паролю. Значит, это не прежний password drift между `users` и `control_license_users`.

Кодовый путь:

- `PATCH /api/settings/license-accounts/{login}` принимает `password`;
- `update_license_user()` передавал любое непустое значение в `_pg_update_user()`;
- `_pg_update_user()` хешировал строку без проверки качества/placeholder;
- frontend показывает placeholder `пароль установлен`, но backend до фикса не защищал себя от случайного non-empty значения.

## Вывод

Root cause: server-side admin password update boundary был слишком доверчивым. Любое непустое значение могло стать новым реальным паролем и синхронно попасть в `users` и `control_license_users`.

## Исправление

- Live пароль `Artem` восстановлен через `utils.license.set_user_password()`.
- В `utils/license.py` добавлен `_validate_new_password()`.
- Backend теперь отклоняет:
  - пустой пароль;
  - пароль короче 10 символов;
  - placeholders `пароль установлен`, `не задан`;
  - маски вида `********` / `••••••`.
- Валидация применяется в:
  - `set_user_password()`;
  - `_pg_update_user()`;
  - legacy `update_license_user()` path.
- Добавлен regression test `tests/test_license_password_validation.py`.

## Следующий шаг

При следующем auth-инциденте сначала проверять три независимых слоя:

- пароль проверяется через `utils.license.validate_user()`;
- hash совпадает в `users` и `control_license_users`;
- последний admin PATCH не отправлял `password` со служебным placeholder.
