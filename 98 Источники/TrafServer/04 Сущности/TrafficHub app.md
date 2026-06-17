# TrafficHub app

Теги: #сущность

## Тип

Модуль

## Где находится

`remote_files/traffic_hub/app.py`

## Роль в системе

Регистрирует TrafficHub routers, выполняет миграции и поднимает websocket endpoints. Это точка сборки business API-контурa.

## Входы

- FastAPI app
- роутеры и websocket manager

## Выходы

- `/traffic-api/*`
- `/traffic-ws`
- `/ws`

## Зависимости

- [[TrafficHub database]]
- [[API]]

## Типовые сбои или риски

- router imports расходятся с доступным snapshot;
- неполный локальный source coverage.
