# Leads service

Теги: #сущность

## Тип

Сервис

## Где находится

`remote_server_snapshot/services/leads_service.py`

## Роль в системе

Содержит основную бизнес-логику operational цикла: загрузка конфига, сбор лидов, загрузка в Sheets, рассылка, retry queue, SuperJob и планировщик.
Фактический live-helper для Sheets сейчас `upload_to_sheets`; старый `upload_resumes_to_sheets` в runtime отсутствует и не должен использоваться.

## Формат ссылки резюме Rabota.ru

Подтверждено live-кодом `utils/data_processor.py`: для Rabota.ru откликов поле `Резюме` в Google Sheets должно формироваться в контексте отклика:

`https://www.rabota.ru/resume-search/{resume_id}/?source=response&vacancy_id={vacancy_id}&response_id={response_id}`

Источник ID:

- `resume_id` — `resume.id` или `resume_id`.
- `vacancy_id` — `vacancy.id` или `vacancy_id`.
- `response_id` — `response_id` или `id` отклика.

Fallback `https://www.rabota.ru/resume/{resume_id}` допустим только если для отклика не хватает `vacancy_id` или `response_id`. Новые выгрузки после server commit `898a9a91c` используют новый формат; старые строки в Google Sheets не переписываются автоматически.

## Excel / CSV import-export

Подтверждено server commit `a04351895`: `api/routers/leads.py` расширен форматами `.xlsx` и `.csv`.

- `GET /api/leads/export.xlsx` выгружает owner-scoped лиды текущего пользователя в Excel workbook `leads.xlsx`.
- `POST /api/leads/import` принимает `.xlsx` и `.csv`, нормализует русские/английские заголовки и сохраняет лиды в локальную базу текущего пользователя.
- Импорт использует `require_autolead_access` и `bind_current_username`, поэтому не должен смешивать лиды разных пользователей.
- Импорт не пишет строки напрямую в Google Sheets и не запускает рассылку. Это сделано намеренно: загрузка файла меняет только локальную базу, а отправка остаётся отдельным управляемым действием.

Поддерживаемые смысловые поля импорта:

- `ФИО` / `Имя` / `full_name`
- `Телефон` / `Номер` / `phone`
- `Email` / `Почта`
- `Вакансия`
- `Город`
- `Пол`
- `Дата`
- `Возраст`
- `Дата рождения`

## Входы

- user config
- Rabota.ru tokens
- Google Sheets credentials
- локальная runtime БД

## Выходы

- новые лиды
- записи в `autolead.db`
- обновления Sheets
- send/retry статистика

## Зависимости

- [[Runtime database]]
- [[Control store]]

## Типовые сбои или риски

- конфиг drift;
- сложные fallback-ветки;
- shared lock `_cycle_running`.
- несовместимость между сервисным слоем и helper API Sheets при отставании server runtime от кода;
- stale job state после падения фазы, если не сбрасывать owner-scoped queue state отдельно от логов.
- Leads.su/Воксис может иногда отдавать пустой DOM после редиректа. Подтверждено live debug HTML: нормальная страница содержит `#vacancy_form` и `#send_form`, failing-снимок был пустым `<body>`. Для этого в `modules/platforms/leadsu.py` нужен recovery перед permanent `form-failure`: повторное открытие landing, стабилизация формы и direct-submit fallback. См. [[2026-06-20 leadsu voxys submit recovery]].
- Retry-фаза может зависнуть не из-за очереди, а из-за одного платформенного `fill()` без общего дедлайна. Runtime-защита: `modules/vbiv_bot.py` ограничивает заполнение одного оффера дефолтом 180 секунд, а live progress хранит отдельное поле `processed`. См. [[2026-06-20 retry queue hang and live dashboard progress]].

## Связанные расследования

- [[2026-06-29 Rabota response resume link format]]
- [[2026-06-29 Leads Excel import export]]
