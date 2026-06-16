# Хранилища и runtime артефакты

## Подтверждённые storage-контуры

### 1. Operational SQLite

Используется legacy Autolead runtime:

- `leads`
- `send_history`
- `invite_history`
- `retry_queue`
- `run_log`
- `app_log`
- `control_sync_queue`

Ключевой модуль: `utils/database.py`.

Поверх него уже введён промежуточный boundary:

- `utils/runtime_repository.py`

На 2026-06-15 он покрывает часть owner-scoped чтения/сброса для:

- leads list/export/resend
- dashboard summary/history
- debug recent leads
- `traffic_hub` bridge list/export/KPI/chart/finance proxy

### 2. PostgreSQL

Используется для:

- `control_*`
- пользователей, ролей, per-user config, auth
- `traffic_hub` SQLAlchemy-моделей
- части CRM/integration сущностей

### 3. Redis

Используется для:

- owner-scoped queue/state
- coordination между web и worker

## Runtime-артефакты

Желаемые operational директории:

- `data/runtime`
- `data/runtime/secrets`
- `data/logs`
- `data/debug`
- `data/backups`
- `secrets`
- `AccountManager/data`

## Технический долг

В live-репозитории в корне всё ещё подтверждены legacy runtime-артефакты:

- `.env`
- `autolead.db`
- Windows `.exe`

Это не каноническая целевая схема, а исторический долг, который нельзя убирать большим движением без отдельного maintenance-окна.

## Вывод

Текущая модель не “всё уже migrated в PostgreSQL”.

Фактическая модель:

- `traffic_hub` и control plane — PostgreSQL-first;
- Autolead operational runtime — SQLite-first;
- queue/state coordination — Redis.

## См. также

- [[материалы/документы/TrafficHub-obsidian/02 Архитектура/Структура репозитория]]
- [[материалы/документы/TrafficHub-obsidian/05 Решения/PostgreSQL control store]]
- [[материалы/документы/TrafficHub-obsidian/05 Решения/Не делать big-bang миграцию SQLite в PostgreSQL]]
