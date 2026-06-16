# Google Sheets Sync

Файл: `modules/sheets_sync.py` (536 строк)

## Библиотека

`gspread` — Google Sheets API client.

## Функции

- Чтение/запись Google Sheets
- Дедупликация по телефону и email
- Batch upload с rate-limit handling
- Экспорт истории лидов
- Экспорт детальных резюме кандидатов в отдельную вкладку `Резюме`
- Чтение offers из sheets (legacy)

## Формат данных

Лиды выгружаются в структурированные таблицы:
- Дата, время, ФИО, телефон, email, вакансия, город, статус

Отдельно для каждого цикла собираются raw-резюме из Rabota.ru и пишутся в лист `Резюме` того же workbook:
- `Дата`
- `Источник`
- `Resume ID`
- `Response ID`
- `Vacancy ID`
- `Фио`
- `Телефон`
- `Почта`
- `Город`
- `Пол`
- `Возраст`
- `Дата рождения`
- `Вакансия`
- `Обновлено`
- `Опыт`
- `Образование`
- `Гражданство`
- `Переезд`
- `Командировки`
- `Метро`
- `Резюме`

## Сервисный аккаунт

Файл: `secrets/service_account.json`

Runtime-факт:
- у пользователя может быть отдельный `google_sheets.service_account_file`
- для `alex` используется `/app/data/runtime/secrets/service_account__alex.json`
- это делает Sheets-экспорт owner-scoped, если профиль реально подхватывается через `bind_current_username(...)`

## Fail-closed при недоступных role workbook

Подтверждено 2026-06-10:
- `pending_spreadsheet_id` и `processed_spreadsheet_id` могут быть недоступны текущему service account;
- `gspread.open_by_key(...)` возвращает `PermissionError`;
- `modules/sheets_sync.py::_open_spreadsheet()` не fallback'ится на основной `google_sheets.spreadsheet_id`;
- если role workbook недоступен или не задан, операция завершается fail-closed и пишет диагностический лог;
- это защищает main workbook от смешивания очередей `pending/processed` разных назначений.

Ограничение:
- код не восстанавливает доступ автоматически;
- нужно дать service account доступ к конкретному role workbook или заменить `pending_spreadsheet_id` / `processed_spreadsheet_id`.

## Ограничение размера ячеек

Google Sheets не принимает ячейку больше 50 000 символов.

Для вкладки `Резюме` используется `_MAX_SHEETS_CELL_CHARS = 49000`:
- длинный текст обрезается;
- в конец добавляется `... [обрезано]`;
- это предотвращает падение батча резюме из-за одного большого кандидата.

## Связанное

- [[материалы/документы/TrafficHub-obsidian/01-Architecture/DataFlow|Data Flow]]
- [[материалы/документы/TrafficHub-obsidian/04-Database/autolead|autolead.db]]
