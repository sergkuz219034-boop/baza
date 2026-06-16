# 2026-06-16 Третий шаг миграции retry_queue в PostgreSQL

## Симптом

После переноса `app_log/run_log` и `send_history` таблица `retry_queue` оставалась в SQLite. Это сохраняло hybrid runtime в самой критичной части full cycle: повторные попытки после ошибок партнёрских форм.

## Зона системы

- `utils/database.py`
- `utils/runtime_store_delivery.py`
- `utils/runtime_store_pg_delivery.py`
- `services/leads_service.py`
- PostgreSQL таблица `autolead_retry_queue`
- SQLite таблица `retry_queue`

## Гипотеза

`retry_queue` можно перенести третьим этапом, если сохранить семантику:

- `UNIQUE(owner_username, phone, offer_name)`;
- повторный `add_to_retry_queue` увеличивает `retry_count`;
- записи с `retry_count >= max_retries` не возвращаются в due retries;
- `remove_from_retry_queue` удаляет запись после успешной отправки;
- `get_retry_queue_size` считает только активные записи.

## Проверка

Проверены текущие вызовы:

- `services/leads_service.py::process_retry_queue`
- `utils/database.py::{add_to_retry_queue,get_due_retries,remove_from_retry_queue,get_retry_queue_size,clear_retry_queue}`
- `utils/runtime_store_delivery.py`

Найден дополнительный дефект:

- `process_retry_queue` формировал ключ `phone:offer_name`, а `send_history` хранит owner-scoped ключ `owner:phone:offer_name`.
- Это могло мешать удалению устаревших retry-записей, если отправка уже есть в истории.

## Наблюдение

`utils/runtime_store_pg_delivery.py` расширен таблицей:

- `autolead_retry_queue`

Перенос данных:

- SQLite `retry_queue`: 436 строк
- PostgreSQL `autolead_retry_queue`: 436 строк
- Summary по `owner_username/offer_name/platform/retry_count/max_retries` совпал.

Runtime-проверка после rebuild/restart:

- `admin` active retry size: 55
- `admin` due retries: 55
- тестовая запись `DebugOffer` изменила счётчик `55 -> 56 -> 55`
- `pg retry rows`: 436
- targeted tests: `39 passed`

## Вывод

`retry_queue` переведён на PostgreSQL. Теперь `send_history` и `retry_queue` находятся в одном PostgreSQL delivery backend, а SQLite fallback сохранён для тестов и аварийного отката.

Оставшиеся SQLite-backed таблицы:

- `leads`
- `invite_history`
- `invite_message_state`
- `autofit_seen`
- `control_sync_queue`

## Следующий шаг

Следующий этап: мигрировать `leads`, потому что она крупнее и участвует в выгрузке, dedup, analytics и выборе кандидатов для рассылки.

Связанные страницы:

- [[Второй шаг миграции send_history в PostgreSQL]]
- [[Мигрировать Autolead runtime поэтапно начиная с логов]]
- [[PostgreSQL и SQLite hybrid runtime]]
