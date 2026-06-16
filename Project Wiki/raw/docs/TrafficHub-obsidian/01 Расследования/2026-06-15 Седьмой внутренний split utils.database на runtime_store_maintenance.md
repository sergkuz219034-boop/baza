# 2026-06-15 Седьмой внутренний split `utils.database` на `runtime_store_maintenance`

## Симптом

После выноса logs, delivery, invites, control sync, leads и autofit `utils/database.py` всё ещё держал retention/cleanup path:

- `clear_entire_database`
- `prune_old_data`

Это был последний крупный operational block внутри legacy runtime store.

## Зона системы

- legacy SQLite runtime
- `utils/database.py`
- cleanup / retention path

## Гипотеза

Maintenance-блок можно вынести в отдельный internal module без смены внешнего API, если сначала добавить прямые tests на его поведение.

## Проверка

Сначала в `tests/test_database.py` добавлены прямые maintenance tests.

Далее на live source сервера:

- добавлен `utils/runtime_store_maintenance.py`;
- `utils/database.py` переведён на делегирование для функций:
  - `clear_entire_database`
  - `prune_old_data`

Прогнаны проверки:

- `python3 -m compileall -q utils/runtime_store_maintenance.py utils/database.py api traffic_hub services modules config main.py`
- `python3 -m pytest -q tests/test_database.py -q`

## Наблюдение

- `compileall` прошёл.
- `tests/test_database.py` прошёл.
- Внешние импорты через `utils.database` сохранены.

## Вывод

Седьмой safe internal split подтверждён. Operational реализация legacy runtime store теперь почти полностью вынесена в отдельные internal modules, а `utils.database.py` стал в основном:

- compatibility facade
- schema/init/migration helper
- low-level shared helper layer

## Следующий шаг

1. Оценить, нужно ли отдельно выделять `init_db` / schema migration helpers.
2. Если нет, переключаться на следующий god-file за пределами `utils.database.py`.
