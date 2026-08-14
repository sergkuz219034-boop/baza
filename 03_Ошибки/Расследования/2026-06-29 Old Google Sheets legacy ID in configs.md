# 2026-06-29 Old Google Sheets legacy ID in configs

## Симптом

Пользователь спросил, почему лиды уходили в старую Google-таблицу:

`10tCmh8ZFbHhmNohrZRNedfY81K2_olYJnjk623HRnMY`

## Зона системы

- `control_user_app_configs.config_json->google_sheets`
- `modules/sheets_sync.py`
- `services/leads_service.py::upload_sheets`
- owner-scoped Google Sheets настройки

## Гипотеза

Старая таблица могла оставаться в legacy-поле `google_sheets.spreadsheet_id` или в старых user-profile config, а часть старого кода могла использовать это поле как fallback.

## Проверка

На live PostgreSQL найдено:

- `admin.google_sheets.spreadsheet_id` содержал старый ID.
- `admin.google_sheets.pending_spreadsheet_id` уже был правильный: `1seCE2MPKZV01LJMvL4CuvSDL7IdG-V_vN6hmqoAcZOs`.
- `admin.google_sheets.processed_spreadsheet_id` уже был правильный: `1vu2zNVWqMAl_jU3gs8AgCeDTxIFhvXHt1U5tHLID4m8`.
- `artem.google_sheets.pending_spreadsheet_id` и `processed_spreadsheet_id` были правильные.
- Старый ID также оставался у неактивных/старых профилей `artem3000`, `seregalys`, `audit-user-a`, `bob`.

Кодовая проверка:

- `services/leads_service.py::upload_sheets()` передает `spreadsheet_role="pending"`.
- `modules/sheets_sync.py::_sheet_role_config()` для `pending` использует `pending_spreadsheet_id`, без legacy fallback.
- Старый `spreadsheet_id` всё ещё может быть опасен для старых функций чтения/очистки или для профилей, где `pending_spreadsheet_id` пустой.

## Наблюдение

Причина старых попаданий в эту таблицу: legacy-настройки Google Sheets жили в user configs и раньше могли наследоваться/использоваться вместо owner-specific `pending_spreadsheet_id`.

Текущий код после owner-scope фикса не должен писать pending-лиды Artem в старый `spreadsheet_id`, если у Artem заполнен `pending_spreadsheet_id`.

## Вывод

Старый ID был не hardcoded production fallback, а runtime-конфиг в PostgreSQL. У активного `admin` он лежал в legacy-поле `spreadsheet_id`, хотя рабочие `pending/processed` поля уже были правильными.

Выполнена санитарная live-правка:

- `admin.google_sheets.spreadsheet_id = ""`
- `admin.google_sheets.spreadsheet_name = ""`

Рабочие поля не изменялись:

- `pending_spreadsheet_id`
- `processed_spreadsheet_id`

## Следующий шаг

Если старую таблицу снова откроет новый job, проверить owner job-а и его `control_user_app_configs.google_sheets`. Особое внимание на старые профили, где `pending_spreadsheet_id` пустой или равен старому workbook.

## Связанные заметки

- [[Zarplata.ru integration]]
- [[2026-06-29 Unified Rabota and Zarplata dispatch order]]
