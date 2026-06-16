# 2026-06-17 Live control_store backend

## Симптом

После разметки `P3` оставался вопрос, который нельзя было закрывать только по коду:

- какой backend реально использует `control_store` на live-хосте;
- означает ли наличие `control.db`, что control contour ещё работает на SQLite;
- насколько `CONTROL_PG_LEGACY_IMPORT=false` отражается в реальном runtime.

## Зона системы

- live repo `/root/TrafficHub`
- контейнер `autolead_server_bot`
- `utils/control_store.py`

## Гипотеза

Если live `control_store` уже PostgreSQL-first, то:

- `utils.control_store.health()` должен вернуть `backend=postgres`;
- `legacy_import_enabled` должен быть `false`;
- наличие `control.db` на диске не должно трактоваться как active SQLite backend.

## Проверка

На live-хосте внутри `autolead_server_bot` выполнен:

- `from utils.control_store import health; print(health())`

Получен ответ:

- `ok=True`
- `backend='postgres'`
- `db_path='/app/data/runtime/control.db'`
- `legacy_import_enabled=False`
- `legacy_sqlite_exists=True`
- `users=4`
- `configs=15`
- `legacy_configs=1`
- `auth=7`
- `legacy_auth=1`
- `history=6291`

## Наблюдение

- active `control_store` backend на live уже PostgreSQL;
- `CONTROL_PG_LEGACY_IMPORT=false` реально выключает legacy import path;
- `control.db` файл всё ещё существует, но это не делает SQLite активным backend;
- наличие `legacy_configs` и `legacy_auth` counters показывает, что control contour всё ещё несёт compatibility-следы, даже при PostgreSQL-first backend.

## Вывод

На `2026-06-17` `control_store` надо описывать так:

- active backend: PostgreSQL;
- legacy SQLite artefact: существует;
- legacy import path: выключен;
- `control.db` нельзя использовать как shorthand-доказательство того, что live control contour сидит на SQLite.

## Следующий шаг

1. Поднять live status `control_store` в краткий канон.
2. Зафиксировать, что `P3` — это не active SQLite backend, а PostgreSQL-first control contour с legacy artefact trail.
3. При отдельном cleanup stream решать уже не "перенос на PostgreSQL", а судьбу оставшихся legacy artefacts и compatibility counters.
