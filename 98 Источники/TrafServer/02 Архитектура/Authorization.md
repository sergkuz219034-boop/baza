# Authorization

Теги: #архитектура

## Роли

По коду подтверждены две эффективные роли:

- `admin`
- `user` / `operator`

`viewer` и `operator` нормализуются в обычного пользователя.

## Как применяются права

- Dashboard API использует `require_authenticated`, `require_operator`, `require_admin`.
- TrafficHub API использует `get_current_user`, `require_operator`, `require_admin`.
- AccountManager допускает только `admin`.

## Почему авторизация завязана на данные

Даже при успешном входе обычный пользователь видит только свои записи:

- scope идёт через `owner_username`;
- admin видит глобальный срез;
- обычный пользователь получает owner-scoped выборки и `404` на чужие записи.

## Смежные страницы

- [[Authentication]]
- [[Multi-Tenant]]
