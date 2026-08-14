# БАГ-012: у пользователя пустые `google_sheets` overrides затирали глобальные таблицы

## Симптом

У `kursmerkusheva@gmail.com` при открытии/добавлении таблиц Google Sheets не подхватывались pending/processed spreadsheet IDs из базового конфига.

## Зона системы

- `services/leads_service.py`
- `utils.control_store`
- user-scoped `config.json` в `control_user_app_configs`
- `google_sheets` merge при `load_config()`

## Гипотеза

Пустые строковые поля в user profile (`pending_spreadsheet_id`, `processed_spreadsheet_id`, `spreadsheet_id` и связанные name-поля) затирали значения из базового конфига при `_deep_merge_dicts(base, profile)`.

## Проверка

- В runtime у пользователя был валиден `google_sa_json`.
- `load_config_local()` содержал заполненные base IDs:
  - `pending_spreadsheet_id`
  - `processed_spreadsheet_id`
- `control_store.load_user_config("kursmerkusheva@gmail.com")` возвращал те же ключи пустыми строками.
- После merge user profile обнулял base таблицы.

## Наблюдение

Фикс сделан в `_load_user_config_profile()`:

- перед merge пустые `google_sheets.*spreadsheet*` overrides удаляются из user profile, если в fallback уже есть непустое значение;
- `service_account_file` остаётся user-scoped;
- глобальные таблицы теперь снова видны этому пользователю.

## Вывод

Канон для `google_sheets`:

- user profile не должен обнулять базовые spreadsheet IDs пустыми строками;
- если пользователь ещё не настроил свои таблицы, он должен видеть глобальные значения;
- пустые overrides допустимы только там, где они не ломают merge.

## Следующий шаг

- при необходимости добавить отдельную UI-индикацию, когда spreadsheet IDs берутся из base config, а не из user profile.
