# Control user storage

## Назначение

`control_*` таблицы в PostgreSQL хранят данные, перенесённые из legacy `control.db`, и используются как совместимый слой для лицензий, пользовательских настроек и секретов TrafficHub.

## Таблицы

- `control_license_users` — license/account слой для логина, роли, активности и клиентской метки.
- `control_user_app_configs` — user-scoped настройки приложения.
- `control_user_app_auth` — user-scoped секреты и OAuth/auth данные.
- `control_app_configs` и `control_app_auth` — старый HWID-scoped слой; на 2026-06-29 пустой в live runtime.

## Ownership

Канонический список текущих пользователей лежит в `users`.

Для актуального runtime правило такое:

- запись в `control_user_app_configs.login` должна соответствовать `users.username` без учёта регистра;
- запись в `control_user_app_auth.login` должна соответствовать `users.username` без учёта регистра;
- запись в `control_license_users.login` должна соответствовать `users.username` без учёта регистра.

Если записи в `control_*` не имеют пары в `users`, это legacy orphan, а не рабочий пользователь.

## Проверка orphan-записей

Повторяемая проверка:

```sql
select c.login
from control_user_app_configs c
where not exists (
  select 1 from users u where lower(u.username) = lower(c.login)
);

select a.login
from control_user_app_auth a
where not exists (
  select 1 from users u where lower(u.username) = lower(a.login)
);

select l.login
from control_license_users l
where not exists (
  select 1 from users u where lower(u.username) = lower(l.login)
);
```

## Подтверждённое состояние

На 2026-06-29 live-сервер был очищен от orphan-записей:

- `control_user_app_configs`: удалено 11 legacy orphan-записей;
- `control_user_app_auth`: orphan-записей не было;
- `control_license_users`: orphan-записей не было.

Backup удалённых строк лежит на сервере:

`/home/codex/TrafficHub_backup_archive/20260629-093800-legacy-accounts-cleanup/`

## Ограничения

Таблицы `control_*` всё ещё нужны для совместимости: их нельзя просто удалить как класс без переписывания авторизации, настроек и миграционного слоя.

UI-подпись `TrafficHub_Licenses` историческая. Источник истины для валидности аккаунта — наличие пользователя в `users` и отсутствие orphan-записей в `control_*`.
