# Job Timeline

## Что это
Persistent append-only журнал событий job поверх текущего Redis/job state.

## Таблица
`autolead_job_events`

Ключевые поля:
- `owner_username`
- `job_id`
- `command`
- `event_type`
- `status`
- `ts`
- `progress_json`
- `message`
- `error`
- `payload_json`

## Endpoint
`GET /api/jobs/timeline?limit=&job_id=`

Дополнительно для admin:

`GET /api/jobs/timeline?owner=artem&limit=30`

## Ownership
Обычный пользователь видит только свои job-события, даже если передаст `owner` другого пользователя. Admin может передать `owner` явно и смотреть timeline нужного профиля.

## UI
В `Admin панель` есть admin-only карточка `Диагностика runtime`, внутри неё блок `История задач`:

- пустой owner = текущий пользователь;
- заполненный owner работает только для admin;
- выводятся последние события, статус, команда, сообщение и ошибка.

## Почему не только Redis
Redis хранит быстрый текущий state. Для расследования зависших и завершённых job нужна persistent история после refresh/restart API.

## Связанные файлы
- `/root/TrafficHub/traffic_hub/services/job_queue.py`
- `/root/TrafficHub/utils/runtime_store_pg_jobs.py`
- `/root/TrafficHub/utils/database.py`
- `/root/TrafficHub/api/routers/jobs.py`
- `/root/TrafficHub/dashboard/index.html`
- `/root/TrafficHub/dashboard/app.js`

## Связанные заметки
- [[Runtime database]]
- [[Runtime Inspector]]
