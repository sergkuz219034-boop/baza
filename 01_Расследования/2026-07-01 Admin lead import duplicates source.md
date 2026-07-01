# 2026-07-01 Admin lead import duplicates source

## Симптом

В UI `База лидов` после импорта файла показано:

- `Импортировано в базу: 0`
- `прочитано строк: 21 259`
- `дублей/уже были: 21 259`
- `Показано 50 из 22 815 записей`

Пользователь спросил, из какой базы система видит эти лиды как уже существующие.

## Зона системы

- `api/routers/leads.py::import_leads_file()`
- `utils/database.py::save_leads()`
- `utils/runtime_store_pg_leads.py::save_leads()`
- `utils/runtime_repository.py::list_owned_leads()`
- PostgreSQL table `autolead_leads`

## Гипотеза

Импорт файла сравнивается не с текущим содержимым Google Sheets, а с локальным owner-scoped PostgreSQL read-model `autolead_leads`.

## Проверка

- `api/routers/leads.py::import_leads_file()` считает `duplicates_or_existing = len(leads) - saved`.
- `saved` приходит из `utils.database.save_leads()`, который в live runtime пишет в PostgreSQL `autolead_leads`.
- `autolead_leads` имеет unique constraint:
  - `(owner_username, phone, vacancy_id, lead_date)`.
- Для Excel/CSV импорта `api/routers/leads.py::_normalize_import_row()` ставит:
  - `_source_type = excel`;
  - `_raw_data = row`;
  - `vacancy_id` в `save_leads()` становится `0`.
- `utils/runtime_repository.py::list_owned_leads()` для UI `База лидов` читает только owner rows через `WHERE owner_username=%s`.

Runtime 2026-07-01:

- `autolead_leads` total: `30 549`;
- `admin`: `22 815`;
- `admin/source_type=excel`: `20 291`;
- `admin/source_type=response`: `2 520`;
- `admin/source_type=zarplata`: `4`;
- все `admin/source_type=excel` были собраны в PostgreSQL в `2026-06-29 17:59:43`.

## Наблюдение

Скрин `Показано 50 из 22 815 записей` совпадает с количеством строк `admin` в `autolead_leads`. Значит UI показывает не Google Sheets и не общую базу всех пользователей, а локальную PostgreSQL базу лидов конкретного owner `admin`.

## Вывод

`дубли уже были: 21 259` означает: все строки импортируемого файла совпали с уже существующими строками `admin` в `autolead_leads` по ключу `phone/email + vacancy_id=0 + lead_date`. Это не ошибка Google Sheets API. Это локальная дедупликация TrafficHub перед/вместе с импортом.

Отдельный слой Google Sheets тоже может дедуплицировать при `upload_sheets()`, но число на скрине относится именно к PostgreSQL `autolead_leads`.

## Следующий шаг

Если нужно повторно залить такой файл как новые лиды, нельзя просто импортировать тот же файл: нужно либо очистить/архивировать старые `admin/source_type=excel` строки в `autolead_leads`, либо изменить бизнес-ключ импорта. Перед чисткой обязателен backup PostgreSQL и понимание, что эти строки уже участвуют в UI-истории и matching.

## Дополнение 2026-07-01: результат импорта разделён на local DB и Google Sheets

### Симптом

Старая строка UI показывала только `Импортировано в базу` и `дублей/уже были`, из-за чего пользователь видел `0` и считал, что файл не попал в Google Sheets.

### Проверка

- `api/routers/leads.py::import_leads_file()` уже вызывал `upload_sheets(config, leads)` даже если `save_leads(leads)` вернул `0`.
- `dashboard/app.js::importLeadsFile()` не показывал `uploaded_to_sheets` и `sheets_duplicates_or_existing`.

### Вывод

Фактическая логика уже смотрела в Google Sheets через `upload_sheets()`, но UI скрывал этот слой. Пользовательский контракт был неверным: локальный дубль не должен визуально перекрывать результат проверки Google Sheets.

### Фикс

- Product commit `4adba7a4a`: API возвращает отдельные поля `local_duplicates_or_existing`, `google_sheets_duplicates_or_existing`, `google_sheets_checked`.
- UI показывает две части:
  - `локальная база: +N, уже были M`;
  - `Google Sheets: +A, уже были B`.
- Regression test закрепляет сценарий: локальная база вернула `0`, но Google Sheets получил и добавил строку.
