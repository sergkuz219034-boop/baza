# Backend

Теги: #архитектура

## Основные backend-модули

- `remote_server_snapshot/services/leads_service.py`
- `remote_server_snapshot/utils/database.py`
- `remote_files/utils/control_store.py`
- `remote_files/utils/license.py`
- `remote_files/traffic_hub/app.py`
- `remote_files/traffic_hub/models/database.py`
- `remote_server_snapshot/AccountManager/database/*`
- `remote_server_snapshot/AccountManager/api/routers/*`
- `remote_server_snapshot/AccountManager/services/*`

## Что делает каждый слой

- `leads_service.py` содержит бизнес-логику цикла, конфигов, scrape/upload/send/retry/schedule.
- `utils/database.py` хранит runtime-state с owner scoping.
- `control_store.py` хранит лицензии, per-user config и auth payloads.
- `license.py` объединяет legacy Google Sheets compatibility и новый control-store-first подход.
- `api/routers/settings.py` собирает settings UI из двух источников: общий runtime config и per-user auth из control store. Rabota credentials для `user` читаются и сохраняются отдельно от общего `config.json`.
- `TrafficHub` обслуживает async SQLAlchemy модели и `/traffic-api/*`.
- `AccountManager` теперь содержит отдельный sync SQLAlchemy backend scaffold под Telegram, Google и social account modules.

## Почему backend сложный

- проект эволюционировал из локального runtime в multi-service систему;
- часть legacy-поведения сохранена ради миграций;
- tenant isolation добавлялся постепенно миграциями, а не был вшит с первого дня.

## Смежные страницы

- [[Database]]
- [[API]]
- [[Multi-Tenant]]
