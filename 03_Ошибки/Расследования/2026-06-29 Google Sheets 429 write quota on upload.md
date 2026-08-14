# 2026-06-29 Google Sheets 429 write quota on upload

## Симптом

Во время выгрузки лидов в Google Sheets UI показывал:

- `Sheets upload failed after 3 attempts`
- `APIError: [429]: Quota exceeded for quota metric 'Write requests'`
- `В Sheets добавлено строк: 0`

## Зона системы

- `services/leads_service.py`
- `modules/sheets_sync.py`
- live worker `traffichub_worker`

## Гипотеза

Проблема не в данных лидов и не в авторизации Google, а в слишком большом количестве отдельных write-запросов при одной выгрузке.

## Проверка

1. Проверен live код `services/leads_service.py`: выгрузка идёт через `upload_sheets()` -> `modules.sheets_sync.upload_to_sheets()`.
2. Проверен live код `modules/sheets_sync.py`:
   - `upload_to_sheets()` после дедупликации вызывает `_insert_rows_chronologically(...)`;
   - старый `_insert_rows_chronologically()` делал `worksheet.insert_rows(...)` по группам дат и батчам;
   - каждая такая вставка была отдельным write-запросом в Google Sheets API.
3. В логике уже был retry, но он не лечил первопричину, потому что повторял тот же паттерн множества write-запросов.
4. На live сервере заменён алгоритм:
   - строки собираются и вставляются в память в правильное место;
   - затем лист переписывается одной массовой `worksheet.update(...)` операцией на диапазон данных;
   - при необходимости заранее расширяется число строк `worksheet.add_rows(...)`.
5. Проверка после патча:
   - `py_compile` для `modules/sheets_sync.py` прошёл;
   - in-memory smoke показал один `update()` вместо серии `insert_rows()`;
   - файл подложен в `traffichub_app` и `traffichub_worker`;
   - контейнеры перезапущены;
   - health приложения внутри контейнера вернул `status=ok`.

## Наблюдение

- Лимит бился именно по `Write requests per minute per user`.
- Старый путь `insert_rows()` был дорогим по числу API-вызовов, особенно если в выгрузке несколько дат или несколько пачек.
- Даже корректный retry не помогает, если сама операция раздроблена на много отдельных writes.

## Вывод

Первопричина — архитектура записи в Sheets, а не временный сетевой сбой.

Исправление: массовая перестройка листа одной записью вместо серии `insert_rows()` существенно снижает число write-запросов и должна убрать типовой `429` при обычной выгрузке.

## Следующий шаг

- Проверить следующую реальную выгрузку на бою и убедиться, что `В Sheets добавлено строк` снова растёт без `429`.
- Если лимит повторится, следующая зона проверки — другие пути записи в Sheets (`append_log_to_sheet`, processed/pending queue updates), а не только первичная выгрузка.
