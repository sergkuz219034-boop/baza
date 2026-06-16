# 2026-06-16 Четвертый шаг миграции leads в PostgreSQL

## Симптом

После миграции `app_log/run_log`, `send_history` и `retry_queue` таблица `leads` оставалась в SQLite. Это сохраняло главный runtime-кэш лидов в старой БД, а dashboard/bridge могли читать устаревшую SQLite-копию.

## Зона системы

- `utils/database.py`
- `utils/runtime_store_leads.py`
- новый файл `utils/runtime_store_pg_leads.py`
- `utils/runtime_repository.py`
- PostgreSQL таблица `autolead_leads`
- SQLite таблица `leads`

## Гипотеза

`leads` можно переносить после delivery-state, если:

- сохранить dedup constraint `owner_username, phone, vacancy_id, lead_date`;
- сохранить public API `utils.database`;
- перевести не только core storage, но и `utils/runtime_repository.py`, который обслуживает dashboard/bridge;
- оставить SQLite fallback для тестов и аварийного отката.

## Проверка

Проверены зависимости:

- `utils/runtime_store_leads.py`: `save_leads`, `load_leads_for_send`, `get_existing_phones`, `get_latest_lead_meta_by_phones`, `get_leads_stats`, `clear_leads`.
- `utils/runtime_repository.py`: списки лидов, export, summary/history, bridge rows, charts, finance proxy.
- `api/routers/leads.py`, `services/stats_service.py`, `traffic_hub/services/autolead_bridge.py` используют `runtime_repository`.

## Наблюдение

Добавлен feature flag:

- `AUTOLEAD_RUNTIME_LEADS_BACKEND=postgres`

Добавлен PostgreSQL backend:

- `autolead_leads`

Перенос данных:

- SQLite `leads`: 19834 строки
- PostgreSQL `autolead_leads`: 19834 строки
- Summary по `owner_username/source_type` совпал.

Runtime-проверка:

- `admin` leads: 789
- `admin` existing phones: 775
- `admin` leads for send за 30 дней: 789
- sample meta по телефону `+79778491153` вернул `vacancy_id/response_id/resume_id/source_type`
- repository `list_owned_leads('admin')`: 789
- repository summary: `processed_today=38`, `offers_today=Онекта 37, Воксис 1`
- `Ozon` не вернулся в успешные отправки, потому что его строки остались `unconfirmed`.
- targeted tests: `39 passed`

## Вывод

`leads` переведён на PostgreSQL вместе с dashboard/bridge repository reads. Теперь основные runtime-таблицы Autolead находятся в PostgreSQL:

- `autolead_app_log`
- `autolead_run_log`
- `autolead_send_history`
- `autolead_retry_queue`
- `autolead_leads`

SQLite ещё используется для оставшихся вспомогательных таблиц:

- `invite_history`
- `invite_message_state`
- `autofit_seen`
- `control_sync_queue`

## Следующий шаг

Следующий этап: мигрировать `autofit_seen`, затем `invite_history/invite_message_state`, затем `control_sync_queue`. После этого SQLite можно будет оставить только как legacy fallback/import или удалить из active runtime.

Связанные страницы:

- [[Третий шаг миграции retry_queue в PostgreSQL]]
- [[Мигрировать Autolead runtime поэтапно начиная с логов]]
- [[PostgreSQL и SQLite hybrid runtime]]
