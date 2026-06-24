# TrafficHub app

## Legacy dashboard

После commit `fd205a4fe` старый `/traffic/*` не считается рабочим UI-контуром. Он оставлен только как backward-compatible redirect в основной dashboard.

Канонический UI для раздела `TrafficHub` находится внутри основного dashboard и открывается через hash routes `#crm-*`.

См. [[TrafficHub legacy dashboard отключён]].

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
