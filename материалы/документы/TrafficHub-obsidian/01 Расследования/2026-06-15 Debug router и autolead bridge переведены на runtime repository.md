# 2026-06-15 Debug router и autolead bridge переведены на runtime repository

## Симптом

- После первого boundary-этапа прямой SQLite ещё оставался в:
  - `api/routers/debug.py`
  - `traffic_hub/services/autolead_bridge.py`

## Зона системы

- `api/routers/debug.py`
- `traffic_hub/services/autolead_bridge.py`
- `utils/runtime_repository.py`

## Гипотеза

Если перевести и эти два потребителя на `runtime_repository`, то в верхних слоях `api` и `traffic_hub` прямой SQLite останется только в migration/import сценариях.

## Проверка

- `runtime_repository` расширен под:
  - debug recent leads
  - bridge list/export
  - bridge KPI/chart/finance proxy
- После правки выполнены:
  - `grep` по `api` и `traffic_hub`
  - `python3 -m compileall -q api traffic_hub utils services modules config main.py`
  - `python3 tools/repo_hygiene_check.py --strict`

## Наблюдение

- В `api` и `traffic_hub` прямой SQLite остался только в `traffic_hub/migrations.py`.
- Это ожидаемо: migration/import слой и должен уметь читать legacy SQLite напрямую.

## Вывод

Boundary cleanup для верхних слоёв на этом этапе закрыт:

- `api/routers/leads.py`
- `api/routers/debug.py`
- `services/stats_service.py`
- `traffic_hub/services/autolead_bridge.py`

Теперь основной SQLite-знание локализовано лучше и меньше размазано по API/bridge коду.

## Следующий шаг

- Следующий разумный шаг уже не в ширину, а в глубину:
  - разбор `utils/database.py`
  - выделение подмодулей/репозиториев внутри legacy runtime store
  - без одновременной миграции в PostgreSQL
