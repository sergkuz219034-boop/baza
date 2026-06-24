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

## Ownership
Обычный пользователь видит только свои job-события. Это важно для multi-tenant isolation и расследований чужих логов.

## Почему не только Redis
Redis хранит быстрый текущий state. Для расследования зависших и завершённых job нужна persistent история после refresh/restart API.

## Связанные файлы
- `/root/TrafficHub/traffic_hub/services/job_queue.py`
- `/root/TrafficHub/utils/runtime_store_pg_jobs.py`
- `/root/TrafficHub/utils/database.py`
- `/root/TrafficHub/api/routers/jobs.py`

## Связанные заметки
- [[Runtime database]]
- [[Runtime Inspector]]

