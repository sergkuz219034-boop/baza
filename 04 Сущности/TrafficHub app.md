# TrafficHub app

## Legacy dashboard

После commit `fd205a4fe` старый `/traffic/*` не считается рабочим UI-контуром. Он оставлен только как backward-compatible redirect в основной dashboard.

Канонический UI для раздела `TrafficHub` находится внутри основного dashboard и открывается через hash routes `#crm-*`.

После commit `4873a176b` hash routes `#crm-*` мапятся на отдельные tab-pane, а не на Autolead-разделы:

- `#crm` -> `tab-crm-overview`
- `#crm-leads` -> `tab-crm-leads`
- `#crm-messengers` -> `tab-crm-messengers`
- `#crm-funnels` -> `tab-crm-funnels`
- `#crm-networks` -> `tab-crm-networks`
- `#crm-finance` -> `tab-crm-finance`
- `#crm-analytics` -> `tab-crm-analytics`
- `#crm-settings` -> `tab-crm-settings`

Это важно для UX: раздел `TrafficHub` больше не должен показывать Autolead `leads/offers/stats/settings` под CRM-названиями.

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
- основной dashboard `/#crm-*`
- backward-compatible redirect `/traffic/*` -> `/#crm-*`

## Зависимости

- [[TrafficHub database]]
- [[API]]

## Типовые сбои или риски

- router imports расходятся с доступным snapshot;
- неполный локальный source coverage.
- повторное смешивание `crm-*` с Autolead tab-pane приведёт к тому, что пользователь увидит не тот раздел при клике в sidebar.
