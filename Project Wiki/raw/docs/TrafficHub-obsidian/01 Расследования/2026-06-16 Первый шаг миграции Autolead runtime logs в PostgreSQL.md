# 2026-06-16 Первый шаг миграции Autolead runtime logs в PostgreSQL

## Симптом

В проекте уже есть PostgreSQL, но Autolead runtime продолжал хранить operational state в SQLite `data/runtime/autolead.db`. Это создавало два источника истины и путало диагностику логов, статусов запусков и счётчиков.

## Зона системы

- `utils/database.py`
- `utils/runtime_store_logs.py`
- новый файл `utils/runtime_store_pg_logs.py`
- `docker-compose.yml`
- контейнеры `autolead_server_bot`, `traffichub_worker`, `traffichub_postgres`

## Гипотеза

Самый безопасный первый шаг миграции — перенести не критичные для доставки лидов таблицы логов:

- `app_log`
- `run_log`

Причина: эти таблицы важны для observability, но не являются первичным operational queue для отправки форм. `leads`, `send_history`, `retry_queue` пока остаются в SQLite до отдельной миграции.

## Проверка

Проверены текущие runtime-файлы на сервере `/root/TrafficHub`:

- `utils/database.py` уже делегирует операции в `utils/runtime_store_*`.
- `utils/runtime_store_logs.py` содержит SQLite-backed функции для `app_log/run_log`.
- `docker-compose.yml` уже передаёт `DATABASE_URL` в `autolead_bot` и `worker`.
- `requirements.txt` содержит `psycopg[binary]>=3.2.0`.

## Наблюдение

Добавлен feature flag:

- `AUTOLEAD_RUNTIME_LOGS_BACKEND=postgres`

Добавлен PostgreSQL backend:

- `autolead_app_log`
- `autolead_run_log`

В `utils/database.py` public API не изменён. Функции `append_app_log`, `get_app_logs`, `clear_app_log`, `start_run`, `finish_run`, `get_recent_runs`, `clear_run_log` выбирают PostgreSQL backend только при включённом флаге. SQLite fallback сохранён.

Перед включением backend данные перенесены из SQLite в PostgreSQL:

- `app_log`: 1362 строки
- `run_log`: 172 строки

Runtime-проверка через `utils.database` подтвердила запись и чтение нового лога `admin` из PostgreSQL.

## Вывод

Первый низкорисковый шаг миграции выполнен: runtime logs больше не обязаны жить в SQLite. Это не завершает полную миграцию Autolead runtime, потому что критичные таблицы `leads`, `send_history`, `retry_queue` ещё остаются SQLite-backed.

## Следующий шаг

Следующий безопасный этап: мигрировать `send_history` в PostgreSQL с dual-read/dual-write или feature flag. После этого dashboard-счётчики отправок и история партнёрских форм перестанут зависеть от SQLite.

Связанные страницы:

- [[Runtime repository boundary для legacy SQLite]]
- [[PostgreSQL и SQLite hybrid runtime]]
- [[Send]]
