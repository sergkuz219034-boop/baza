# БАГ-014 Google Sheets настройки пользователя наследовали admin/base таблицы

## Симптом

У пользователя `alex` в настройках отображались названия таблиц `admin`, хотя ID таблиц были пользовательскими.

## Зона системы

- `services/leads_service.py`
- `api/routers/settings.py`
- `api/routers/settings_sheets.py`
- PostgreSQL `control_user_app_configs`
- Google Sheets settings: `pending_spreadsheet_id`, `processed_spreadsheet_id`, `pending_spreadsheet_name`, `processed_spreadsheet_name`

## Гипотеза

Проблема не в UI. `GET /api/settings` получает уже загрязнённый merged config после `load_config()`.

## Проверка

Live diagnostic внутри `autolead_server_bot` сравнил:

- raw `control_user_app_configs` для `admin`;
- raw `control_user_app_configs` для `alex`;
- результат `services.leads_service.load_config()` под `bind_current_username("alex")`.

Факт:

- raw config `alex` содержал свои `pending_spreadsheet_id` / `processed_spreadsheet_id`;
- raw config `alex` имел пустые `pending_spreadsheet_name` / `processed_spreadsheet_name`;
- после `load_config()` имена стали `RabotaRu_Leads_Pending` / `RabotaRu_Leads_Export` из admin/base config.

## Наблюдение

Причина в `_strip_empty_google_sheet_overrides()`:

- helper удалял пустые user-specific `*_spreadsheet_name`;
- после этого `_deep_merge_dicts(base, profile)` подставлял имена из base/admin config;
- раньше тот же механизм мог подставить и `pending/processed_spreadsheet_id`, если user profile держал пустые ID.

## Вывод

Это multi-tenant isolation bug. Поля направления выгрузки Google Sheets должны быть owner-owned и не наследоваться из admin/base config:

- `spreadsheet_id`;
- `pending_spreadsheet_id`;
- `processed_spreadsheet_id`;
- `spreadsheet_name`;
- `pending_spreadsheet_name`;
- `processed_spreadsheet_name`.

Shared fallback допустим только для технического `service_account_file`, если пользователь не загрузил свой JSON и общий service account имеет доступ к его таблице.

## Исправление

- `_strip_empty_google_sheet_overrides()` больше не удаляет пустые user-specific spreadsheet IDs.
- Пустые spreadsheet names сохраняются, если у пользователя указан собственный spreadsheet ID.
- Добавлены regression tests:
  - `test_empty_user_google_sheets_ids_do_not_inherit_base_tables`;
  - `test_empty_user_spreadsheet_names_do_not_inherit_base_names_for_user_tables`;
  - `test_user_google_sheets_merge_keeps_owner_specific_targets_only`.

## Следующий шаг

При новых жалобах “таблица не та” проверять:

- raw `control_user_app_configs` конкретного login;
- merged `load_config()` под `bind_current_username(login)`;
- фактические `pending/processed_spreadsheet_id` в runtime перед записью в Sheets.
