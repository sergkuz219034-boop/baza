# 2026-06-15 Runtime repository boundary для legacy SQLite

## Симптом

- `api/routers/leads.py` держал raw SQL прямо внутри роутера.
- `services/stats_service.py` держал owner-scoped SQLite-аналитику внутри service-файла.
- Любая правка storage-логики требовала лезть в верхний слой.

## Зона системы

- `api/routers/leads.py`
- `services/stats_service.py`
- `utils/database.py`
- новый `utils/runtime_repository.py`

## Гипотеза

Даже без миграции с SQLite можно снизить связность, если вынести owner-scoped runtime-доступ в отдельный compatibility boundary.

## Проверка

- Выполнен live-code review на сервере.
- Введён `utils/runtime_repository.py`.
- На него переведены:
  - `api/routers/leads.py`
  - `services/stats_service.py`
- После правки выполнены:
  - `python3 -m compileall -q api modules services utils traffic_hub config main.py`
  - `python3 tools/repo_hygiene_check.py --strict`
  - `docker compose config`

## Наблюдение

- Верхние слои перестали держать часть прямого SQLite SQL.
- Поведение runtime не менялось.
- SQLite остался operational storage, но знание о его деталях стало локальнее.

## Вывод

Это не миграция БД, а boundary cleanup.

Практический результат:

- следующие storage-изменения теперь проще делать через один слой;
- reasoning по owner-scoped leads/stats стал чище;
- можно постепенно переводить и другие потребители.

## Следующий шаг

- Рассмотреть перевод:
  - `api/routers/debug.py`
  - `traffic_hub/services/autolead_bridge.py`
- Не трогать одновременно storage migration и worker/runtime orchestration.
