# 2026-06-15 Первый внутренний split `utils.database` на `runtime_store_logs`

## Симптом

`utils/database.py` оставался одним из крупнейших legacy-файлов runtime store и продолжал смешивать:

- schema/init;
- leads cache;
- retry queue;
- send history;
- app log;
- run log;
- служебные owner-aware helper-ы.

Это делало безопасный рефакторинг дорогим: любое изменение в logs/run history требовало заходить в общий god-file.

## Зона системы

- legacy Autolead runtime store
- `utils/database.py`
- UI/logging слой, который читает `app_log` и `run_log`

## Гипотеза

Самый безопасный первый внутренний split — вынести `app_log` и `run_log` в отдельный подмодуль без смены публичного API, а `utils.database` оставить как compatibility facade.

## Проверка

Проверен live source на сервере:

- добавлен новый модуль `utils/runtime_store_logs.py`;
- `utils/database.py` переведён на делегирование для функций:
  - `clear_run_log`
  - `append_app_log`
  - `get_app_logs`
  - `clear_app_log`
  - `start_run`
  - `finish_run`
  - `get_recent_runs`
- внешние импорты в кодовой базе оставлены прежними через `utils.database`.

После split выполнены проверки:

- `python3 -m compileall -q utils/runtime_store_logs.py utils/database.py api traffic_hub services modules config main.py`
- `python3 -m pytest -q tests/test_database.py -q`

## Наблюдение

- Публичный контракт не менялся.
- Внешние callers не пришлось переписывать.
- Тесты `tests/test_database.py` прошли.
- Это уже не repository boundary верхнего уровня, а именно внутренний decomposition внутри legacy storage слоя.

## Вывод

Первый безопасный internal split подтверждён: logs/run-history можно выносить из `utils.database.py` поэтапно, не ломая runtime и не меняя старые импорты.

Это снижает размер god-file и подготавливает следующий шаг: вынос `retry_queue` и `send_history`.

## Следующий шаг

1. Выделить следующий безопасный блок внутри `utils.database.py`:
   - `retry_queue`
   - `send_history`
2. Сохранить паттерн compatibility facade через `utils.database`.
3. После каждого split синхронизировать:
   - `README.md`
   - `CHANGELOG.md`
   - server docs
   - локальную wiki
