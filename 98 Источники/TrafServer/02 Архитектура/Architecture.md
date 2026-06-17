# Architecture

Теги: #архитектура

## Подсистемы

### 1. Autolead runtime

- вход: `remote_server_snapshot/main.py`
- сервисный слой: `services/leads_service.py`
- хранение: `autolead.db`
- функции: scheduler, scraper, upload, sender, retry queue, cleanup

### 2. Worker

- вход: `remote_server_snapshot/traffic_hub/worker.py`
- отдельный контейнер `worker`
- выполняет owner-scoped job queue отдельно от web-процесса
- пишет `worker.heartbeat` для Docker healthcheck

### 3. Dashboard API

- подтверждён по `api/routers/jobs.py` и `api/routers/settings.py`
- управляет job lifecycle, настройками, лицензиями, импортом/экспортом и destructive cleanup
- полный entrypoint отсутствует в snapshot, но `main.py` импортирует `api.server`

### 4. TrafficHub API

- вход: `remote_files/traffic_hub/app.py`
- хранение: `traffic_dashboard.db` через SQLAlchemy
- публикует `/traffic-api/*` и websocket `/traffic-ws`, `/ws`

### 5. License Auth

- контейнер `license_auth`
- внешний auth issuer для bearer token сценариев

### 6. License Server

- контейнер `license_server`
- отдельный server-side license API
- использует RSA ключи лицензирования

### 7. AccountManager

- вход: `remote_server_snapshot/AccountManager/api/main.py`
- отдельная БД `accounts.db`
- admin-only API и static dashboard

## Поток данных

1. Пользователь проходит auth.
2. Конфиг и auth payload читаются из PostgreSQL-first control store; `control.db` остаётся legacy snapshot/import surface.
3. Web-контейнер ставит job в owner-scoped очередь.
4. Worker исполняет цикл отдельно.
5. Лиды попадают в runtime БД.
6. Sheets и внешние интеграции обновляются как вторичные поверхности.
7. TrafficHub API работает с отдельной business schema.

## Архитектурные ограничения

- несколько auth boundary в одном deployment;
- несколько SQLite/data planes;
- частичный snapshot исходников;
- смешение operational и business контуров в одном compose.
- compatibility layer для старых runtime secret paths временно нужен ради исторических config payload.

## Смежные страницы

- [[Backend]]
- [[Database]]
- [[Authentication]]
- [[Security]]
