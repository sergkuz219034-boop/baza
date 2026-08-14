# 2026-06-29 Legacy accounts cleanup

## Симптом

В системе остались старые legacy-аккаунты и user-scoped конфиги, которые больше не соответствуют актуальным пользователям TrafficHub.

## Зона системы

PostgreSQL runtime storage:

- `users`
- `control_license_users`
- `control_user_app_configs`
- `control_user_app_auth`

Связанные зоны: [[Control user storage]], [[Multi-Tenant]].

## Гипотеза

После миграции legacy `control.db` в PostgreSQL в `control_user_app_configs` могли остаться тестовые и старые логины, которых уже нет в актуальной таблице `users`. Такие записи могут путать админку, настройки и диагностику.

## Проверка

На live-сервере `/root/TrafficHub` проверены:

- список контейнеров через `docker compose ps`;
- схемы таблиц PostgreSQL через `information_schema.columns`;
- текущие логины в `users`;
- старые логины в `control_license_users`, `control_user_app_configs`, `control_user_app_auth`;
- таблица `accounts` AccountManager.

Факт runtime: основной контейнер `traffichub_app` и PostgreSQL `traffichub_postgres` были healthy на момент проверки.

## Наблюдение

В `control_user_app_configs` были найдены orphan-записи, которых нет в `users`:

- `artem2`
- `artem3000`
- `audit-admin`
- `audit-user-a`
- `audit-user-b`
- `bob`
- `operator`
- `seregalys`
- `sergey`
- `system`
- `user`

В `control_user_app_auth` orphan-записей не было.

В `control_license_users` orphan-записей не было.

В `accounts` AccountManager остались только текущие Telegram-аккаунты; legacy orphan-записей там не найдено.

## Действие

Перед удалением создан server-side CSV backup:

`/home/codex/TrafficHub_backup_archive/20260629-093800-legacy-accounts-cleanup/`

Затем из `control_user_app_configs` удалены 11 orphan-записей.

## Вывод

Legacy orphan-аккаунты были не в основной таблице пользователей, а в старом user-scoped config storage. Рабочие пользователи из `users`, активные license-аккаунты и AccountManager-аккаунты не тронуты.

После удаления:

- `remaining_config_orphans = 0`
- `remaining_auth_orphans = 0`
- `remaining_license_orphans = 0`

## Следующий шаг

Если в админке снова появятся старые логины, проверять не только `users`, но и `control_user_app_configs`/`control_user_app_auth` на orphan-записи. UI-текст `TrafficHub_Licenses` является совместимой исторической подписью, а не отдельным источником старых аккаунтов.
