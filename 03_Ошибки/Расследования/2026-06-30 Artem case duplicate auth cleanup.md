# 2026-06-30 Artem case duplicate auth cleanup

## Симптом

- В live-БД одновременно существовали `Artem` и `artem`.
- Это могло проявляться как рассинхрон роли, tenant membership и owner-scoped настроек.
- Типовой пользовательский симптом: настройки/таблицы/роль выглядят так, будто подтянулись не из своего контура.

## Зона системы

- Auth/authz: `api/authz.py`, `traffic_hub/authz.py`.
- PostgreSQL: `users`, `control_license_users`, `tenant_memberships`, owner-scoped таблицы.
- Runtime owner model Autolead/TrafficHub.

## Гипотеза

- Система уже нормализует owner username в lower-case во многих runtime-путях, но `ensure_license_user()` и `ensure_external_user()` искали `users.username` case-sensitive.
- При входе с другим регистром можно было создать второй `User` для того же человека.

## Проверка

- Live SQL показал два пользователя:
  - `users.id=2 username=Artem role=admin`;
  - `users.id=25 username=artem role=admin`;
  - оба были в `tenant_memberships` как owner одного tenant.
- `control_license_users` содержал один аккаунт `Artem` с ролью `user`.
- Runtime data была в основном под owner `artem`.
- Код до фикса:
  - `traffic_hub/authz.py::ensure_license_user()` делал `select(User).where(User.username == username)`;
  - `traffic_hub/authz.py::ensure_external_user()` делал такой же case-sensitive lookup.

## Наблюдение

- Причина подтверждена кодом и live-БД.
- Простая правка live-БД без изменения кода была бы временной: следующий вход с другим регистром мог снова создать дубль.

## Вывод

- Исправление должно быть на auth-boundary:
  - canonical username для auth-created users — lower-case;
  - поиск пользователя — case-insensitive;
  - если уже есть lowercase-дубль, он выбирается первым, чтобы не падать на unique constraint.
- Live cleanup:
  - создан backup `audit_user_case_cleanup_20260630`;
  - удалён дубль `users.id=25`;
  - `users.id=2` переведён в `username=artem`, `role=user`;
  - `control_license_users.login` переведён в `artem`;
  - `network_integrations.owner_username` нормализован в `artem`.

## Следующий шаг

- При похожих симптомах первым check выполнять:
  - `select lower(username), count(*), string_agg(username, ', ') from users group by lower(username) having count(*) > 1;`
  - `select lower(login), count(*), string_agg(login, ', ') from control_license_users group by lower(login) having count(*) > 1;`
- Если результат пустой, искать причину уже в owner-scoped config или Google Sheets credentials.

## Подтверждение

- Product commit: `382050ae7 fix: canonicalize auth usernames`.
- Tests: `396 passed, 43 skipped`.
- GitHub checks for commit `382050ae7`: `CI` success, `Build and Push Docker Image` success.
- Live deploy: `traffichub_app` и `traffichub_worker` пересозданы.
- Runtime health: `/api/health` вернул `status=ok`.
- Post-deploy SQL:
  - дублей в `users` по `lower(username)` нет;
  - дублей в `control_license_users` по `lower(login)` нет;
  - `artem` существует одной строкой с ролью `user`.

