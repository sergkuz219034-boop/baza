# Поток API

## Подтверждённые точки входа

- `api/server.py`
- `api/routers`
- `traffic_hub/app.py`

## Подтверждённые API-группы

- `auth`
- `finance`
- `funnels`
- `integrations`
- `leads`
- `messengers`
- `offers`
- `postbacks`
- `stats`
- `tools`
- `tracking`

## Реальный flow

1. browser session или HTTP Basic попадает в `api/server.py`
2. `api/routers/*` обрабатывают основной dashboard/API path
3. `traffic_hub/app.py` монтирует embedded `/traffic-api/*`
4. job/status/log bridge связывает web/API и worker через Redis
5. Account Manager использует отдельный bridge endpoint `/api/account-manager/token`

## Что устарело

- отдельную активную SPA `/traffic` считать устаревшей моделью;
- websocket не считать независимым token-auth API path.

## Глубокие ссылки

- [[Project Wiki/08_API/Внутреннее API|Внутреннее API]]
- [[Project Wiki/raw/docs/TrafficHub-obsidian/03-API/Overview|Legacy API overview]]
- [[Project Wiki/raw/docs/TrafficHub-obsidian/03-API/Endpoints|Legacy API endpoints]]
