# 2026-06-29 Excel import to Sheets

## Симптом

Загрузка лидов через Excel/CSV добавляла строки только во внутреннюю CRM-базу TrafficHub, но не добавляла их в общую Google Sheets таблицу.

## Зона системы

- `api/routers/leads.py`
- `modules/sheets_sync.py`
- `services/leads_service.py`
- `autolead_leads`
- Google Sheets queue-лист `Все лиды`

Связанные сущности: [[Leads service]], [[Google Sheets integration]].

## Гипотеза

Endpoint `POST /api/leads/import` нормализует файл и вызывает только `save_leads()`. Если после этого не вызвать общий Sheets writer, импортированные лиды не попадут в рабочую очередь Google Sheets и не будут видны в общей таблице.

## Проверка

На сервере `/root/TrafficHub` проверен код:

- `api/routers/leads.py` — импорт `.xlsx`/`.csv`;
- `modules/sheets_sync.py` — общий writer в Google Sheets;
- `services/leads_service.py::upload_sheets()` — production-путь выгрузки в основную таблицу.

Подтверждено: `modules/sheets_sync.py` уже умеет:

- дедуплицировать по телефону/email;
- учитывать отработанную таблицу;
- вставлять строки хронологически по колонке `Дата`;
- не создавать новые вкладки.

## Наблюдение

До правки `POST /api/leads/import` возвращал только:

- `saved_to_db`
- `duplicates_or_existing`

После `save_leads()` не было вызова `upload_sheets()`.

## Решение

`POST /api/leads/import` теперь:

1. читает `.xlsx`/`.csv`;
2. нормализует строки в формат Autolead;
3. сохраняет лиды в owner-scoped CRM DB;
4. загружает те же нормализованные лиды в owner-scoped основную Google Sheets таблицу через `services.leads_service.upload_sheets()`;
5. возвращает отдельные счётчики CRM и Sheets.

Новый ответ включает:

- `saved_to_db`
- `duplicates_or_existing`
- `uploaded_to_sheets`
- `sheets_duplicates_or_existing`
- `sheets_error`, если CRM сохранилась, а Sheets upload упал.

## Вывод

Excel/CSV импорт теперь работает как ручное добавление лидов в рабочую очередь: строки попадают и в CRM, и в общую Google Sheets таблицу. Классификация по датам делается существующим Sheets writer по колонке `Дата`.

## Следующий шаг

Если понадобится автоматический запуск рассылки после Excel-импорта, это нужно делать отдельным явным действием/переключателем. Сейчас импорт только добавляет лиды в CRM и Sheets, но не запускает заполнение анкет сам по себе.
