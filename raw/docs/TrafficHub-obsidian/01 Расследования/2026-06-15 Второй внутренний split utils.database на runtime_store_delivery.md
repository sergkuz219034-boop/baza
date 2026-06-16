# 2026-06-15 Второй внутренний split `utils.database` на `runtime_store_delivery`

## Симптом

После выноса `app_log` и `run_log` `utils/database.py` всё ещё держал в одном файле delivery-логику:

- `send_history`
- `retry_queue`

Это был следующий крупный связный блок legacy SQLite runtime, который продолжал раздувать god-file.

## Зона системы

- legacy Autolead runtime store
- `utils/database.py`
- delivery / retry path
- unit-тесты `tests/test_database.py`

## Гипотеза

`send_history` и `retry_queue` можно вынести во второй внутренний модуль без изменения внешнего API, если оставить `utils.database` как compatibility facade.

## Проверка

На live source сервера:

- добавлен `utils/runtime_store_delivery.py`;
- `utils/database.py` переведён на делегирование для функций:
  - `load_send_history`
  - `add_send_history`
  - `get_avg_fill_time_ms`
  - `get_daily_offer_sends`
  - `clear_send_history`
  - `clear_retry_queue`
  - `add_to_retry_queue`
  - `get_due_retries`
  - `remove_from_retry_queue`
  - `get_retry_queue_size`

Прогнаны проверки:

- `python3 -m compileall -q utils/runtime_store_delivery.py utils/database.py api traffic_hub services modules config main.py`
- `python3 -m pytest -q tests/test_database.py -q`

Дополнительно пробовался `tests/test_retry_queue_matching.py`, но он упёрся в отдельную test-env проблему импорта `pydantic_settings` через `utils.state`, а не в новый storage split.

## Наблюдение

- `compileall` прошёл.
- `tests/test_database.py` прошёл полностью.
- Поведение runtime API не менялось.
- Внешние импорты из `utils.database` сохранены.

## Вывод

Второй безопасный internal split подтверждён. `utils.database.py` уменьшается по частям без big-bang переписывания и без смены SQLite storage.

Одновременно зафиксирован residual issue test environment:

- `tests/test_retry_queue_matching.py` зависит от импорта `utils.state`;
- `utils.state` тянет `traffic_hub.config.settings`;
- в test-env отсутствует `pydantic_settings`.

Это отдельная проблема тестового контура, не блокирующая текущий storage cleanup.

## Следующий шаг

1. Выделить следующий связный блок:
   - `invite_history`
   - `invite_message_state`
2. Отдельно нормализовать test-env для `utils.state` / `pydantic_settings`.
3. Продолжать уменьшать `utils/database.py` только через совместимые wrappers.
