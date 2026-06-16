# Google Sheets

## Назначение

Google Sheets в Autolead используются как два разных user-scoped хранилища:

- `pending` / основная таблица: текущие лиды для обработки;
- `processed` / отработанная таблица: уже обработанные лиды со статусом и офферами.

## Подтверждённые точки кода

- `services/leads_service.py`
- `modules/sheets_sync.py`
- `api/routers/settings.py`

## Runtime contract

- user config читается через `bind_current_username(username) + load_config()`;
- секция `google_sheets` содержит:
  - `pending_spreadsheet_id`
  - `pending_sheet_name`
  - `processed_spreadsheet_id`
  - `processed_sheet_name`
  - `service_account_file`
- От `2026-06-16` queue-path больше не должен fallback-иться в legacy workbook:
  - `pending` и `processed` используют только свои dedicated bindings;
  - если `pending_spreadsheet_id/pending_spreadsheet_name` не заданы, runtime не должен молча открывать `google_sheets.spreadsheet_id`;
  - если `processed_spreadsheet_id/processed_spreadsheet_name` не заданы, runtime не должен молча открывать основной workbook.
- канонический источник основной таблицы:
  - для каждого пользователя runtime сначала обязан брать `google_sheets.pending_spreadsheet_id` и `google_sheets.pending_sheet_name` из его собственных settings;
  - `google_sheets.spreadsheet_id` и `google_sheets.sheet_name` больше не считать допустимым fallback для queue operations `pending/processed`;
  - они остаются legacy-полями совместимости, но не должны перехватывать queue-path.

## Структура листов

- processed/base export fields подтверждены через `settings.EXPORT_FIELDS`:
  - `Фио`
  - `Пол`
  - `Вакансия`
  - `Дата`
  - `Номер`
  - `Почта`
  - `Город`
  - `Возраст`
  - `ДатаРождения`
- main/pending export fields подтверждены через `settings.MAIN_EXPORT_FIELDS`:
  - `Фио`
  - `Пол`
  - `Вакансия`
  - `Дата`
  - `Номер`
  - `Почта`
  - `Резюме`
  - `Город`
  - `Возраст`
  - `ДатаРождения`
- processed лист дополнительно использует поля:
  - `Статус`
  - `Дата отработки`
  - `Офферы`

## Ownership

- таблицы настраиваются per user, но физически могут быть shared между несколькими users;
- основная таблица (`pending` / main) и processed таблица берутся из user-scoped `google_sheets` settings конкретного пользователя;
- это означает:
  - у разных пользователей могут быть разные основные таблицы;
  - любые проверки выгрузки, порядка дат, статусов и колонки `Резюме` нужно делать относительно таблицы, назначенной именно этому пользователю в настройках;
  - нельзя делать выводы по `admin` и автоматически переносить их на `alex` или `artem`, если у них другой `pending_spreadsheet_id`;
- наличие колонки `Резюме` не должно зависеть от “глобальной” таблицы:
  runtime обязан расширять заголовки именно у той основной таблицы, которая назначена текущему пользователю в settings;
- подтверждённый runtime на 2026-06-12:
  - `Artem`, `admin`, `debuglogs` делят один `pending` spreadsheet и один `processed` spreadsheet;
  - поэтому любые правки порядка строк или содержимого в таком spreadsheet видны сразу всем владельцам этой связки.

## Инварианты

- колонка `Дата` должна идти по возрастанию и в `pending`, и в `processed`;
- новые строки больше не должны просто добавляться в конец листа с последующей полной пересортировкой:
  - runtime ищет правильный блок даты;
  - если дата уже есть, вставка идёт после существующих строк этой даты;
  - если даты ещё нет, вставка идёт между более ранними и более поздними датами;
  - порядок внутри одной даты сохраняется по порядку выгрузки/обработки;
- для этого runtime использует вставку строк в лист (`insert_rows`), а не только `append_rows()` + переписывание всего диапазона;
- аудит порядка нужно делать по реальным Google Sheets, а не по локальным JSON;
- сервисный аккаунт берётся из user-scoped `service_account_file`, который runtime подготавливает через `_ensure_user_service_account_file()`.
- сортировка листов по `Дата` не равна фильтрации очереди по `Дата`:
  - если лид уже попал в `pending` или в локальный backlog для `send`, он должен быть отработан независимо от своей даты;
  - дата влияет на порядок строк в листе, но не должна повторно исключать лид из рассылки/отработки.
- `send_range_from/send_range_to` для Google Sheets должны применяться по реальным номерам строк листа `pending`:
  - runtime использует `_sheet_row`, а не индекс уже отфильтрованного списка;
  - внутри диапазона отрабатываются только кандидаты с пустым полем `Статус`;
  - вне диапазона строки не участвуют в текущей отработке, даже если у них нет статуса.
- `Резюме` должно жить только в основной таблице:
  - main/pending использует `settings.MAIN_EXPORT_FIELDS`;
  - processed sheet остаётся на `settings.EXPORT_FIELDS` без колонки `Резюме`;
  - это подтверждено live fix от 2026-06-15.
- direct URL на чужое резюме Rabota.ru не подтверждён OpenAPI:
  - `utils.data_processor._extract_resume_link()` сначала ищет явный URL в raw payload;
  - если его нет, используется fallback `https://www.rabota.ru/resume/{resume_id}`;
  - этот fallback нужно считать runtime-эвристикой, пока не подтверждён точным web-route из живого UI Rabota.ru.
- queue selection для `pending`:
  - любая непустая строка в колонке `Статус` исключает кандидата из обычной отработки;
  - это относится не только к `Отработан/processed`, но и к прикладным статусам вроде `Ошибка`, `Нет номера`, `Иностранный номер`, `Отправлено`, `Дубль`, `Оффер отключен`;
  - повторная обработка таких строк возможна только через отдельную специально реализованную логику, а не через обычный `send/full cycle`.
- skip по номеру не равен `processed`:
  - `Нет номера`
  - `Иностранный номер`
  - `Некорректный номер`
  должны оставаться статусами в основной таблице и не должны переноситься в processed sheet.

## Известные риски

- shared spreadsheet между несколькими users ломает предположение “каждый пользователь владеет своей физической таблицей”;
- ручные правки в Google Sheets всё ещё могут оставить локальные разрывы порядка;
- runtime теперь меньше трогает весь лист целиком, но поведение формул и форматирования всё равно зависит от Google Sheets semantics `insert_rows` и конкретной структуры пользовательской таблицы.

## См. также

- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-12 Порядок дат в Google Sheets]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Send/backlog больше не фильтруется повторно по периоду]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Google Sheets insertion-by-date вместо append в конец]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-16 Worker image drift и queue workbook fallback в legacy spreadsheet]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Резюме кандидата добавлено только в основную Google Sheets таблицу]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Runtime restart-loop после rebuild был вызван missing import threading]]
- [[материалы/документы/TrafficHub-obsidian/05 Решения/Autolead user settings и ownership]]
