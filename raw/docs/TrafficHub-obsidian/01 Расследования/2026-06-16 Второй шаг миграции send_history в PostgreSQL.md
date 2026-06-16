# 2026-06-16 Второй шаг миграции send_history в PostgreSQL

## Симптом

`send_history` оставался в SQLite после переноса runtime logs. Эта таблица влияет на dedup, dashboard-счётчики отправок и дневные лимиты офферов. Из-за SQLite/PostgreSQL hybrid было сложно отличить реальные успешные отправки от локально засчитанных статусов.

## Зона системы

- `utils/database.py`
- `utils/runtime_store_delivery.py`
- новый файл `utils/runtime_store_pg_delivery.py`
- `docker-compose.yml`
- PostgreSQL таблица `autolead_send_history`
- SQLite таблица `send_history`

## Гипотеза

`send_history` можно перенести вторым этапом, если:

- сохранить public API `utils.database`;
- оставить SQLite fallback;
- перенести все существующие статусы, включая `duplicate` и `unconfirmed`;
- не трогать `retry_queue` в этом же шаге.

## Проверка

Сервер `/root/TrafficHub`:

- `utils/runtime_store_delivery.py` содержит операции `load_send_history`, `add_send_history`, `get_avg_fill_time_ms`, `get_daily_offer_sends`, `clear_send_history`.
- `add_send_history` создаёт `control_sync_queue` событие после успешного insert.
- `docker-compose.yml` уже передаёт `DATABASE_URL` в `autolead_bot` и `worker`.

## Наблюдение

Добавлен feature flag:

- `AUTOLEAD_RUNTIME_DELIVERY_BACKEND=postgres`

Добавлен PostgreSQL backend:

- `autolead_send_history`

Перенос данных:

- SQLite `send_history`: 4852 строки
- PostgreSQL `autolead_send_history`: 4852 строки
- Summary по `owner_username/offer_name/status` совпал.

Дополнительно исправлен дефект:

- `get_daily_offer_sends` раньше считал любые статусы, включая `unconfirmed`.
- Теперь SQLite и PostgreSQL backend считают только `status='sent'`.
- Проверка `admin/Ozon`: `0` успешных за день, потому что 26 строк имеют статус `unconfirmed`.
- Проверка `admin/Онекта`: `37` успешных за день.

## Вывод

`send_history` переведён на PostgreSQL без изменения public API. Dashboard и Autolead теперь могут читать историю отправок из PostgreSQL. SQLite fallback сохранён для тестов и аварийного отката.

Критичные таблицы ещё не мигрированы:

- `retry_queue`
- `leads`
- `invite_history`
- `autofit_seen`
- `control_sync_queue`

## Следующий шаг

Следующий этап: мигрировать `retry_queue`, потому что она логически связана с `send_history` и влияет на повторные попытки, Ozon/Voxys errors и full cycle.

Связанные страницы:

- [[Первый шаг миграции Autolead runtime logs в PostgreSQL]]
- [[Мигрировать Autolead runtime поэтапно начиная с логов]]
- [[PostgreSQL и SQLite hybrid runtime]]
