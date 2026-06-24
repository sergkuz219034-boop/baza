# 2026-06-24 старый TrafficHub dashboard открывался по вкладкам

## Симптом
При нажатии на пункты раздела `TrafficHub` открывался второй dashboard по URL `/traffic/...`, например `/traffic/funnels`.

## Зона системы
Frontend navigation текущего dashboard и legacy TrafficHub SPA:

- `/root/TrafficHub/dashboard/app.js`
- `/root/TrafficHub/dashboard/index.html`
- `/root/TrafficHub/api/server.py`
- legacy assets: `/root/TrafficHub/dashboard/traffic/*`

## Гипотеза
Внутренний sidebar использует старый переход на `/traffic/*`, поэтому браузер покидает основной dashboard и загружает legacy React SPA.

## Проверка
Подтверждено кодом: `openCrmSection()` вызывал `window.location.assign('/traffic' + path)`.

Live-проверка после исправления:

- `GET /traffic/funnels` -> `307 Location: /#crm-funnels`
- `HEAD /traffic/funnels` -> `307 Location: /#crm-funnels`
- тесты: `18 passed`
- `doctor.py`: critical ошибок нет

## Наблюдение
Основной dashboard уже имеет внутренние вкладки и hash routing:

- `#crm`
- `#crm-leads`
- `#crm-messengers`
- `#crm-funnels`
- `#crm-networks`
- `#crm-finance`
- `#crm-analytics`
- `#crm-settings`

## Вывод
Legacy `/traffic/*` больше не должен открывать второй dashboard. Все пункты `TrafficHub` открываются через `switchTab(...)` внутри текущего dashboard.

Commit: `fd205a4fe`.

## Следующий шаг
Если потребуется полноценная CRM-логика для `Воронки`, `Мессенджеры`, `Финансы`, её нужно развивать внутри текущего dashboard, а не возвращать legacy SPA.

