# 2026-06-15 Четвертый внутренний split `utils.database` на `runtime_store_control_sync`

## Симптом

После выноса logs, delivery и invite-блоков `utils/database.py` всё ещё держал:

- `control_sync_queue`
- backoff/retry обновления статусов синхронизации
- queue stats

Это оставляло в legacy god-file ещё один самостоятельный operational блок.

## Зона системы

- legacy SQLite runtime
- `utils/database.py`
- `control_sync_queue`
- `utils/control_sync.py`

## Гипотеза

Очередь синхронизации можно вынести в отдельный internal module без смены внешнего API, потому что её функции уже покрываются `tests/test_database.py` и имеют ограниченный круг callers.

## Проверка

На live source сервера:

- добавлен `utils/runtime_store_control_sync.py`;
- `utils/database.py` переведён на делегирование для функций:
  - `enqueue_control_sync`
  - `get_due_control_sync_events`
  - `mark_control_sync_done`
  - `mark_control_sync_failed`
  - `get_control_sync_queue_stats`

Прогнаны проверки:

- `python3 -m compileall -q utils/runtime_store_control_sync.py utils/database.py utils/state.py api traffic_hub services modules config main.py`
- `python3 -m pytest -q tests/test_database.py tests/test_retry_queue_matching.py -q`

## Наблюдение

- `compileall` прошёл.
- `tests/test_database.py` и `tests/test_retry_queue_matching.py` прошли.
- Внешние импорты через `utils.database` сохранены.
- `utils/control_sync.py` не потребовал переписывания callers.

## Вывод

Четвертый безопасный internal split подтверждён. Теперь из `utils/database.py` уже вынесены:

- logs
- delivery
- invites
- control sync queue

Файл остаётся compatibility facade и storage entrypoint, но уже не держит всю operational реализацию в одном месте.

## Следующий шаг

1. Картировать оставшиеся крупные зоны `utils/database.py`:
   - `leads`
   - `autofit_seen`
   - prune/maintenance
2. Не смешивать дальнейший decomposition со сменой БД.
3. Сначала завершить внутреннюю декомпозицию, потом уже решать, какие таблицы реально тащить в PostgreSQL.
