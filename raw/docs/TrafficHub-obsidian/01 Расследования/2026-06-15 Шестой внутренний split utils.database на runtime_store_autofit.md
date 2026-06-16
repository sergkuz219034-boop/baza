# 2026-06-15 Шестой внутренний split `utils.database` на `runtime_store_autofit`

## Симптом

После выноса logs, delivery, invites, control sync и leads `utils/database.py` всё ещё держал отдельный state-блок автоподбора:

- `autofit_seen`
- дедупликация по `resume_id`

## Зона системы

- legacy SQLite runtime
- `utils/database.py`
- autofit dedupe state

## Гипотеза

`autofit_seen` можно вынести в отдельный internal module без смены внешнего API, если сначала добавить прямые tests на этот блок.

## Проверка

Сначала в `tests/test_database.py` добавлены прямые tests для `autofit_seen`.

Далее на live source сервера:

- добавлен `utils/runtime_store_autofit.py`;
- `utils/database.py` переведён на делегирование для функций:
  - `get_seen_autofit_resume_ids`
  - `mark_autofit_resumes_seen`
  - `get_autofit_seen_count`
  - `clear_autofit_seen`

Прогнаны проверки:

- `python3 -m compileall -q utils/runtime_store_autofit.py utils/database.py api traffic_hub services modules config main.py`
- `python3 -m pytest -q tests/test_database.py -q`

## Наблюдение

- `compileall` прошёл.
- `tests/test_database.py` прошёл, включая новые `autofit` tests.
- Внешние импорты через `utils.database` сохранены.

## Вывод

Шестой safe internal split подтверждён. `autofit_seen` больше не живёт как inline implementation внутри `utils/database.py`.

## Следующий шаг

1. Разобрать оставшийся maintenance/path:
   - `clear_entire_database`
   - `prune_old_data`
2. После этого оценить, достаточно ли разложен legacy runtime store для перехода к следующему крупному файлу.
