Симптом

- Пользователи видят чужие логи в TrafficHub.
- В логах есть ошибки Google Sheets, которые относятся к чужим таблицам или общему service account.

Зона

- `api/server.py`
- `api/ws_manager.py`
- `services/leads_service.py`
- `api/routers/settings.py`
- `modules/sheets_sync.py`

Гипотеза

- История логов из общего файла подмешивается всем пользователям без owner-фильтрации.
- Google Sheets service account хранится как общий файл и может перетираться между пользователями.
- User-конфиги наследуют общие Google Sheets поля из fallback-конфига.

Проверка

- Проверен `/api/logs` и `ws /ws/log`: fallback-история из файла объединялась с owner-scoped in-memory логами.
- Проверен upload `service_account.json`: файл сохранялся в общий `secrets/service_account.json`.
- Проверен merge user-профиля: `google_sheets.service_account_file` и spreadsheet id/name подмешивались из fallback.

Наблюдение

- В `api/server.py` fallback логов переименовывался в owner текущего пользователя при merge.
- В `settings.py` загрузка SA-файла не была owner-scoped.
- В `leads_service.py` Google Sheets конфиг мог унаследоваться от общего fallback, что нарушало tenant isolation.
- Для `artem` в control store был `google_sa_json`, для `alex` — не было.

Вывод

- Утечка логов была реальной логической ошибкой на уровне API логов.
- Часть Google Sheets ошибок объяснялась нарушением изоляции auth/config между пользователями.
- Для постоянной истории логов нужен owner-scoped storage, а не общий файл.

Следующий шаг

- Внедрена owner-scoped таблица `app_log` в локальной SQLite.
- `/api/logs` и websocket snapshot теперь читают persistent history из `app_log`.
- Для пользователей без собственного SA требуется отдельная загрузка ключа, общий fallback больше не должен использоваться.
> Historical note
>
> Эта заметка фиксирует промежуточное состояние расследования.
> На момент её написания upload `service_account.json` ещё шёл в общий `secrets/`.
> После последующих правок канонический runtime-path изменён на `data/runtime/secrets/`,
> а общий путь остался только как compatibility layer для старых payload.

Дополнение от 2026-06-09

- Поверх tenant-isolation добавлен отдельный UI-фильтр логов: в интерфейс теперь попадают только фазы, итоговые числа по сбору, дедупликации, Google Sheets, рассылке и реальные ошибки.
- Из UI-ленты скрыты технические строки `run_scraper`, `run_sender`, `Sheets upload:*`, построчная обработка лидов и повторяющиеся мини-итоги retry-очереди.
- Проверка живого `/api/logs` после деплоя показала компактную выдачу вместо сырого потока.
- Дополнительно найден второй ложный negative у Tilda-форм: success-текст был заранее в DOM внутри `.js-successbox` с `display:none`, поэтому `_wait_success()` не видел подтверждение после submit.
- Для `modules/platforms/tilda.py` добавлен явный `success_selector` на видимый `.js-successbox` / `.t-form__successbox`, чтобы Онекта и похожие лендинги корректно считались успешно отправленными.
