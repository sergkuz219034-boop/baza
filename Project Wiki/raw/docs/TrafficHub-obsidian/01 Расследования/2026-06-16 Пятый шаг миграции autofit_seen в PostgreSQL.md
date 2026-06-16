# 2026-06-16 Пятый шаг миграции autofit_seen в PostgreSQL

## Симптом

После переноса `leads`, `send_history`, `retry_queue`, `app_log` и `run_log` SQLite всё ещё оставался active runtime store для истории автоподбора. Это мешало считать Autolead runtime PostgreSQL-first.

## Зона системы

- `utils/database.py`
- `utils/runtime_store_autofit.py`
- `modules/rabota_api.py`
- `services/leads_service.py`
- таблица SQLite `autofit_seen`
- новая таблица PostgreSQL `autolead_autofit_seen`

## Гипотеза

`autofit_seen` можно перенести отдельно от лидов и рассылки, потому что публичный API уже сосредоточен в фасаде `utils.database`, а потребители вызывают функции `get_seen_autofit_resume_ids`, `mark_autofit_resumes_seen`, `get_autofit_seen_count`, `clear_autofit_seen`.

## Проверка

- Добавлен PostgreSQL backend `utils/runtime_store_pg_autofit.py`.
- В `utils/database.py` добавлено переключение через `AUTOLEAD_RUNTIME_AUTOFIT_BACKEND=postgres`.
- В `docker-compose.yml` добавлена переменная `AUTOLEAD_RUNTIME_AUTOFIT_BACKEND`.
- Создана таблица `autolead_autofit_seen`.
- Данные перенесены из SQLite в PostgreSQL.
- Пересобраны и перезапущены `autolead_bot` и `worker`.
- Проверены контейнеры и `/api/health`.

## Наблюдение

Runtime-факты на сервере:

- `autolead_server_bot` — `healthy`.
- `traffichub_worker` — `healthy`.
- `traffichub_postgres` — `healthy`.
- `/api/health` вернул `{"status":"ok","version":"1.2","app":"TrafficHub"}`.
- В PostgreSQL `autolead_autofit_seen`: `704` строки.
- Для `admin`: `28` строк.
- Тестовая строка `debug-autofit-migration` отсутствует после проверки.

Сводка миграции совпала с SQLite:

| owner_username | vacancy_id | count |
|---|---:|---:|
| пусто | пусто | 164 |
| admin | пусто | 28 |
| alex | пусто | 446 |
| artem | пусто | 66 |

## Вывод

`autofit_seen` переведён в PostgreSQL без изменения внешнего API `utils.database`. SQLite fallback сохранён.

Оставшиеся SQLite-backed зоны Autolead runtime:

- `invite_history`;
- `invite_message_state`;
- `control_sync_queue`;
- maintenance-prune код, который ещё знает про SQLite-таблицы.

## Следующий шаг

Разобрать `invite_history` и `invite_message_state`: найти потребителей, перенести storage в PostgreSQL через фасад `utils.database`, выполнить миграцию данных и проверить полный цикл через runtime smoke.
