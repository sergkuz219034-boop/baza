# 2026-06-16 Седьмой шаг миграции control_sync_queue в PostgreSQL

## Симптом

После переноса основных Autolead runtime-таблиц SQLite оставался active store для `control_sync_queue`. Эта очередь принимает события `send_history` и `invite_history` и background sync отправляет их в control store.

## Зона системы

- `utils/database.py`
- `utils/runtime_store_control_sync.py`
- `utils/control_sync.py`
- `utils/control_store.py`
- таблица SQLite `control_sync_queue`
- новая таблица PostgreSQL `autolead_control_sync_queue`

## Гипотеза

`control_sync_queue` можно перенести в PostgreSQL без изменения `utils.control_sync`, если сохранить фасадные функции:

- `enqueue_control_sync`;
- `get_due_control_sync_events`;
- `mark_control_sync_done`;
- `mark_control_sync_failed`;
- `get_control_sync_queue_stats`.

## Проверка

- Добавлен backend `utils/runtime_store_pg_control_sync.py`.
- В `utils/database.py` добавлено переключение через `AUTOLEAD_RUNTIME_CONTROL_SYNC_BACKEND=postgres`.
- В `docker-compose.yml` добавлена переменная `AUTOLEAD_RUNTIME_CONTROL_SYNC_BACKEND`.
- Создана таблица `autolead_control_sync_queue`.
- Данные перенесены из SQLite.
- Выполнен rebuild/restart `autolead_bot` и `worker`.
- Проверены health, runtime queue API и unit-тесты.

## Наблюдение

Runtime-факты на сервере:

- SQLite `control_sync_queue`: `4962` строки.
- PostgreSQL `autolead_control_sync_queue`: `4962` строки.
- Сводка PostgreSQL:
  - `done/send_history`: `4852`;
  - `done/invite_history`: `110`.
- Pending-событий на момент миграции не было.
- После rebuild:
  - `autolead_server_bot` — `healthy`;
  - `traffichub_worker` — `healthy`;
  - `/api/health` — `status=ok`.
- Runtime check:
  - `AUTOLEAD_RUNTIME_CONTROL_SYNC_BACKEND=postgres`;
  - `get_control_sync_queue_stats()` вернул `{'done': 4962}`;
  - debug-событие добавилось, прочиталось через `get_due_control_sync_events`, пометилось done и было удалено.
- Unit suite:
  - `tests/test_database.py tests/test_retry_queue_matching.py` — `39 passed`.

Отдельное наблюдение:

- `utils/control_store.py::append_history_events()` в PostgreSQL-режиме берёт owner из `user_context`, а не из `payload`.
- `utils/control_sync.py` работает в background thread без явного owner context.
- Подтверждён bug: часть `control_campaign_history` могла получать пустой `owner_username`, если sync выполнялся из фонового потока.
- Исправление: `append_history_events()` теперь использует `user_context`, а если он пустой — `payload.owner_username`.
- Runtime check: debug-событие из `autolead_control_sync_queue` записалось в `control_campaign_history` с `owner_username=admin`.

## Вывод

`control_sync_queue` переведена в PostgreSQL. Owner attribution в background sync исправлен. Основные active runtime-таблицы Autolead больше не обязаны писать в SQLite при включённых backend env:

- `AUTOLEAD_RUNTIME_LOGS_BACKEND=postgres`;
- `AUTOLEAD_RUNTIME_DELIVERY_BACKEND=postgres`;
- `AUTOLEAD_RUNTIME_LEADS_BACKEND=postgres`;
- `AUTOLEAD_RUNTIME_AUTOFIT_BACKEND=postgres`;
- `AUTOLEAD_RUNTIME_INVITES_BACKEND=postgres`;
- `AUTOLEAD_RUNTIME_CONTROL_SYNC_BACKEND=postgres`.

SQLite fallback и schema init остаются в коде как совместимость и test backend.

## Следующий шаг

Проверить оставшиеся обращения к SQLite:

- `utils/runtime_store_maintenance.py`;
- `utils/runtime_store_schema.py`;
- прямые `_conn()` вызовы в тестах и maintenance;
- owner attribution в `control_store.append_history_events()`.
