# 2026-06-15 Восьмой внутренний split `utils.database` на `runtime_store_schema`

## Симптом

После выноса всех operational runtime-блоков `utils/database.py` всё ещё держал большой schema/init слой:

- `init_db`
- ownerless-table migrations
- additive migration для `send_history`

Это уже не была прикладная бизнес-логика, но файл всё ещё оставался смешанным entrypoint + DDL/migration implementation.

## Зона системы

- legacy SQLite runtime
- `utils/database.py`
- schema/init/migration path

## Гипотеза

Schema/init слой можно вынести в отдельный internal module без изменения внешнего контракта `utils.database.init_db()`.

## Проверка

На live source сервера:

- добавлен `utils/runtime_store_schema.py`;
- `utils/database.py` переведён на делегирование `init_db()` в новый модуль;
- `tests/conftest.py` по-прежнему вызывает `utils.database.init_db()`, значит test fixture остаётся каноничным потребителем этого entrypoint.

Прогнаны проверки:

- `python3 -m compileall -q utils/runtime_store_schema.py utils/database.py api traffic_hub services modules config main.py`
- `python3 -m pytest -q tests/test_database.py -q`

Дополнительно подтверждено уменьшение файла:

- `utils/database.py`: `404` строк
- `utils/runtime_store_schema.py`: `265` строк

## Наблюдение

- `compileall` прошёл.
- `tests/test_database.py` прошёл.
- Внешний entrypoint `utils.database.init_db()` сохранён.

## Вывод

Восьмой safe internal split завершил основную decomposition работу по `utils/database.py`.

Теперь `utils.database.py` — это в основном:

- compatibility facade
- low-level shared helpers
- entrypoint слой

А operational/schema implementation разнесён по отдельным internal modules.

## Следующий шаг

1. Зафиксировать `utils.database` как разобранный legacy storage facade в архитектурной карте.
2. Переключиться на следующий крупный god-file вне `utils.database.py`.
