# 2026-06-15 Добавлено прямое test coverage для maintenance path

## Симптом

Перед выделением maintenance-логики из `utils/database.py` прямых tests для:

- `clear_entire_database`
- `prune_old_data`

не было.

Это означало, что cleanup/retention path можно было бы разбить только под compile-check, без подтверждения поведения.

## Зона системы

- `tests/test_database.py`
- `utils/database.py`
- maintenance / retention path

## Гипотеза

Для безопасного split нужно сначала добавить прямые tests на:

- очистку owner-scoped рабочих таблиц;
- удаление старых `run_log`, `app_log`, `autofit_seen`;
- удаление `retry_queue` записей с исчерпанными попытками.

## Проверка

В `tests/test_database.py` добавлены:

- `test_clear_entire_database_removes_owner_data`
- `test_prune_old_data_cleans_old_runtime_rows`

После этого прогнано:

- `python3 -m pytest -q tests/test_database.py -q`

## Наблюдение

- Новые maintenance tests проходят.
- Cleanup path теперь имеет прямое поведенческое покрытие.

## Вывод

Это подготовительный инженерный шаг перед выносом maintenance-блока в отдельный internal module.

## Следующий шаг

1. Вынести `clear_entire_database` и `prune_old_data` в отдельный storage-module.
2. Повторно прогнать `tests/test_database.py`.
