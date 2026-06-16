# Control Store

## Роль

Control store отвечает за:

- пользователей;
- роли;
- auth secrets;
- merged app config;
- часть history/sync-логики.

## Подтверждённые факты

- Live health на `2026-06-11` сообщает:
  - `control.backend=postgres`
  - `control.legacy_import_enabled=false`
  - `control.ok=true`
- Live `api/server.py` подтверждает, что `/api/health` публикует поля:
  - `control.backend`
  - `control.legacy_import_enabled`
  - `control.ok`
- Live compose подтверждает:
  - `DATABASE_URL=postgresql+asyncpg://...`
  - `CONTROL_DB_PATH=/app/data/runtime/control.db`
  - `CONTROL_PG_LEGACY_IMPORT=false`
  - `CONTROL_SYNC_ENABLED`
  - `CONTROL_LEGACY_SHEETS_FALLBACK=false`
  - `CONTROL_LEGACY_SHEETS_DUAL_WRITE=false`
- Следствие:
  - legacy Google Sheets и SQLite больше не считать основным источником истины для accounts/config.

## Что осталось legacy

- `CONTROL_DB_PATH=/app/data/runtime/control.db` всё ещё пробрасывается в контейнеры
- это означает, что SQLite-path сохраняется как fallback/migration artifact
- его нельзя автоматически считать мёртвым без проверки конкретного кода и миграционных путей

## Runtime paths

- `RUNTIME_SECRETS_DIR=/app/data/runtime/secrets`
- `CONFIG_FILE=/app/data/runtime/secrets/config.json`
- `TOKEN_FILE=/app/data/runtime/secrets/rabota_tokens.json`
- `AUTOLEAD_ACCESS_FILE=/app/data/runtime/autolead_access.json`

## Связанные модули

- `utils/control_store.py`
- `utils/license.py`
- `utils/control_sync.py`
- `api/authz.py`
- `api/autolead_access.py`

## PostgreSQL runtime-модель

- В PostgreSQL-режиме admin панель читает runtime users через `utils/license.py::_pg_list_accounts()`.
- Источник списка для UI: таблица `users`.
- Таблица `control_license_users` сама по себе не гарантирует, что пользователь исчезнет из admin панели.
- Следствие:
  - частичное удаление из `control_license_users` недостаточно;
  - удаление должно чистить и runtime-запись в `users`, и связанные сущности.

## Подтверждённые зависимости удаления пользователя

- На `2026-06-08` подтверждено, что для безопасного удаления пользователя в PostgreSQL runtime нужно очищать:
  - `control_license_users`
  - `control_user_app_configs`
  - `control_user_app_auth`
  - `tenant_memberships`
  - `funnels`
  - `users`
- Иначе delete падает по FK:
  - `tenant_memberships_user_id_fkey`
  - `funnels_created_by_fkey`

## Ownership и Rabota API

- Критерий "рабочий профиль" для Autolead нельзя выводить из legacy sheet.
- Практический runtime-критерий для Rabota профиля:
  - наличие записи в `control_user_app_auth`
  - наличие `rabota_app_id`
  - наличие `rabota_app_secret`
  - наличие `rabota_access_token`

## Ownership и Google Sheets credentials

- У профиля может быть собственный `google_sheets.service_account_file`.
- Runtime-формат для owner-scoped файла:
  - `/app/data/runtime/secrets/service_account__<username>.json`
- На `2026-06-09` подтверждено на `alex`:
  - `google_sheets.service_account_file = /app/data/runtime/secrets/service_account__alex.json`
- Следствие:
  - проверять доступ к Sheets надо не только по global `service_account.json`, но и по user-scoped файлу, если профиль его подхватывает.

## Ownership и proxy state

- На `2026-06-14` подтверждено, что `rabota_ru.proxy_url` хранится как часть owner-scoped app config в control store.
- Реальная поломка live runtime была вызвана не кодом proxy сам по себе, а мусорным значением в user config:
  - `Artem.rabota_ru.proxy_url = "Artem"`
  - `ARTEM2.rabota_ru.proxy_url = "Artem"`
- После server-side hardening подтверждено:
  - settings API нормализует и валидирует proxy format до сохранения;
  - `modules/vbiv_bot.py` не должен использовать нераспознанный `proxy_url` даже если он попал в storage legacy-путём.
- Следствие:
  - расследование proxy-багов надо начинать не с Playwright, а с чтения owner-scoped runtime config из control store.

## Ownership и retry queue

- На `2026-06-14` подтверждено, что owner-scoped retry может ломаться не только на данных лида, но и на inherited-ограничениях из `offer_mapping`.
- Практический вывод:
  - retry-ветка не должна повторно матчить уже выбранный оффер по `vacancy_ids` / `vacancy_names`
  - иначе owner получает ложный `нет оффера` вместо реальной retry-попытки

## Риск

- Документация, где `control.db` описан как primary source, устарела.
- Для offline-разбора локальный bundle может отставать от live runtime, хотя compose snapshot уже переснят `2026-06-11`.
- Но обратное утверждение `SQLite больше нигде не участвует` тоже пока нельзя считать полностью доказанным.
