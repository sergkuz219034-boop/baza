# 2026-06-15 Пятый внутренний split `utils.database` на `runtime_store_leads`

## Симптом

После выноса logs, delivery, invites и control sync `utils/database.py` всё ещё держал основной owner-scoped путь работы с лидами:

- `save_leads`
- `load_leads_for_send`
- `get_existing_phones`
- `get_latest_lead_meta_by_phones`
- `get_leads_stats`
- `clear_leads`

Это был следующий большой связный operational block.

## Зона системы

- legacy SQLite runtime
- `utils/database.py`
- lead cache / fallback send source
- owner-scoped lead stats

## Гипотеза

Leads read/write path можно вынести в отдельный internal module без смены внешнего API, потому что он уже локализован по ответственности и покрыт `tests/test_database.py`.

## Проверка

На live source сервера:

- добавлен `utils/runtime_store_leads.py`;
- `utils/database.py` переведён на делегирование для функций:
  - `save_leads`
  - `load_leads_for_send`
  - `get_existing_phones`
  - `get_latest_lead_meta_by_phones`
  - `get_leads_stats`
  - `clear_leads`

Прогнаны проверки:

- `python3 -m compileall -q utils/runtime_store_leads.py utils/database.py api traffic_hub services modules config main.py`
- `python3 -m pytest -q tests/test_database.py -q`

Дополнительно попытка прогнать `tests/test_leads_router.py` выявила отдельный test-env разрыв: в системном `python3` на сервере отсутствует `fastapi`, поэтому router-tests нельзя использовать как прямую smoke-проверку этого storage split.

## Наблюдение

- `compileall` прошёл.
- `tests/test_database.py` прошёл.
- Внешние импорты через `utils.database` сохранены.
- Ошибка `tests/test_leads_router.py` связана с окружением, а не с новым `runtime_store_leads.py`.

## Вывод

Пятый safe internal split подтверждён. `utils.database.py` теперь в значительной степени стал compatibility facade, а не местом хранения всей operational реализации SQLite runtime.

## Следующий шаг

1. Выделить оставшиеся зоны:
   - `autofit_seen`
   - prune/maintenance
   - возможно `clear_entire_database`
2. Отдельно определить каноничное test environment для router/API тестов.
