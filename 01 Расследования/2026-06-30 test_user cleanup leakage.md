# 2026-06-30 test_user cleanup leakage

## Симптом

- В live PostgreSQL появился `test_user`, хотя это не рабочий пользователь.
- Следы были не в `users`/`control_license_users`, а в runtime-таблицах:
  - `control_user_app_configs`: 1 строка;
  - `autolead_leads`: 4 строки.

## Зона системы

- `tests/conftest.py`
- PostgreSQL runtime tables
- test cleanup при запуске pytest против live-like PostgreSQL

## Гипотеза

- После предыдущего исправления `alice` cleanup удалял только `alice`.
- Fixture `test_db` использует `test_user` как owner для части legacy/runtime тестов.
- При запуске pytest внутри контейнера с PostgreSQL backend такой owner мог попасть в live runtime.

## Проверка

- Live SQL подтвердил:
  - `users where username=test_user = 0`;
  - `control_license_users where login/client=test_user = 0`;
  - `control_user_app_configs where login=test_user = 1`;
  - `autolead_leads where owner_username=test_user = 4`.
- `tests/conftest.py` до фикса содержал `_TEST_IDENTITY_LOGINS = {"alice"}`.
- `test_db` fixture задаёт `utils.user_context.get_current_username -> "test_user"`.

## Наблюдение

- Это не пользовательская регистрация и не product-flow.
- Это test identity leakage в runtime storage.
- Host pytest может не иметь доступа к live Postgres, если `settings.database_url` указывает на `localhost:5432`; контейнерный pytest с `DATABASE_URL=postgres:5432` имеет доступ и должен чистить сам.

## Вывод

- Cleanup должен включать `test_user` и удалять не только auth rows, но и owner-scoped runtime rows.
- Cleanup не должен падать на несовпадении схемы: перед delete проверяется наличие таблицы и колонки через `information_schema`.

## Исправление

- Product commit: `6a483516c test: clean leaked test identities from postgres`.
- `tests/conftest.py`:
  - `_TEST_IDENTITY_LOGINS = {"alice", "test_user"}`;
  - cleanup удаляет owner-scoped rows из runtime tables;
  - cleanup удаляет login/username rows из config/auth/support tables;
  - перед delete проверяет наличие колонки.
- Live cleanup:
  - создан backup `audit_test_identity_cleanup_20260630`;
  - удалены 4 строки `autolead_leads`;
  - удалена 1 строка `control_user_app_configs`.

## Подтверждение

- Full pytest на server repo: `396 passed, 43 skipped`.
- GitHub checks for commit `6a483516c`: `CI` success, `Build and Push Docker Image` success.
- Post-cleanup live SQL:
  - `test_user users = 0`;
  - `test_user control_license_users = 0`;
  - `test_user control_user_app_configs = 0`;
  - `test_user autolead_leads = 0`;
  - `alice users = 0`;
  - `alice control_license_users = 0`.

## Следующий шаг

- Если в live снова появляется неизвестный пользователь/owner, первым check делать по всем runtime таблицам, а не только `users`.
- Для новых тестовых identities обязательно добавлять их в `_TEST_IDENTITY_LOGINS`.

