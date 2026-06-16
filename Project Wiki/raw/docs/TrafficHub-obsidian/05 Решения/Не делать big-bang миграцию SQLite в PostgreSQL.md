# Не делать big-bang миграцию SQLite в PostgreSQL

## Проблема

После появления `traffic_hub`, PostgreSQL и Alembic возникла ложная идея, что нужно быстро перенести весь legacy runtime из SQLite в PostgreSQL.

## Контекст

- `traffic_hub/*` уже PostgreSQL-first.
- `utils/control_store.py` уже PostgreSQL-first.
- Но legacy Autolead operational runtime всё ещё работает через `utils/database.py` и SQLite.
- Этот runtime остаётся production-critical: `run`, `upload`, `send`, `full cycle`, logs, retry.

## Решение

Не делать немедленную full migration SQLite -> PostgreSQL как первый шаг.

Сначала:

1. Зафиксировать boundaries между слоями.
2. Убрать прямой storage access из роутеров.
3. Ввести repository/service abstraction.
4. И только потом решать по таблицам, что реально переносить.

## Последствия

- Меньше риск сломать рабочий Autolead runtime.
- Проще reasoning по данным и ownership.
- Можно переносить не весь storage сразу, а только то, что реально даёт эффект.

## Альтернативы

### 1. Перенести всё сразу

Отвергнуто как слишком рискованный шаг для live-сервера.

### 2. Ничего не делать и оставить гибрид как есть

Отвергнуто как плохой путь для сопровождения. Гибрид допустим временно, но boundaries и docs должны быть явными.
