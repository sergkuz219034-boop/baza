# 2026-06-24 старый TrafficHub dashboard открывался по вкладкам

## Симптом
При нажатии на пункты раздела `TrafficHub` открывался второй dashboard по URL `/traffic/...`, например `/traffic/funnels`.

После первого исправления второй dashboard перестал открываться, но содержимое вкладок всё ещё не соответствовало названию раздела: `crm-funnels` показывал Autolead-вакансии, `crm-networks` показывал Autolead-офферы, `crm-settings` открывал общие настройки/secrets.

## Зона системы
Frontend navigation текущего dashboard и legacy TrafficHub SPA:

- `/root/TrafficHub/dashboard/app.js`
- `/root/TrafficHub/dashboard/index.html`
- `/root/TrafficHub/api/server.py`
- legacy assets: `/root/TrafficHub/dashboard/traffic/*`

## Гипотеза
Внутренний sidebar использует старый переход на `/traffic/*`, поэтому браузер покидает основной dashboard и загружает legacy React SPA.

Дополнительная гипотеза после первого фикса: hash routes `crm-*` в `dashboard/app.js` мапятся не на собственные CRM tab-pane, а на существующие Autolead tab-pane.

## Проверка
Подтверждено кодом: `openCrmSection()` вызывал `window.location.assign('/traffic' + path)`.

Live-проверка после исправления:

- `GET /traffic/funnels` -> `307 Location: /#crm-funnels`
- `HEAD /traffic/funnels` -> `307 Location: /#crm-funnels`
- тесты: `18 passed`
- `doctor.py`: critical ошибок нет

Повторная проверка кода подтвердила mismatch:

- `crm` -> `leads`
- `crm-leads` -> `leads`
- `crm-funnels` -> `vacancies`
- `crm-networks` -> `offers`
- `crm-finance` -> `finance`
- `crm-settings` -> `settings`
- `crm-analytics` -> `stats`

Это означало, что пользователь оставался в основном dashboard, но видел не CRM-страницы, а чужие разделы Autolead.

Live-проверка после второго исправления:

- `GET /traffic/networks` -> `307 Location: /#crm-networks`
- главная страница содержит `tab-crm-overview`, `tab-crm-leads`, `tab-crm-messengers`, `tab-crm-funnels`, `tab-crm-networks`, `tab-crm-finance`, `tab-crm-analytics`, `tab-crm-settings`;
- `dashboard/app.js` проходит `node --check`;
- в отданных `index.html` и `app.js` нет mojibake-строк `Р...`;
- `doctor.py --json` вернул `warning`, critical-состояния нет.

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

Дополнительно `crm-*` больше не переиспользуют Autolead tab-pane. Для TrafficHub заведены отдельные внутренние вкладки:

- `crm-overview`
- `crm-leads`
- `crm-messengers`
- `crm-funnels`
- `crm-networks`
- `crm-finance`
- `crm-analytics`
- `crm-settings`

Commit старого dashboard redirect: `fd205a4fe`.
Commit отдельного CRM tab routing: `4873a176b`.

## Следующий шаг
Дальше CRM-логику нужно развивать только внутри новых `crm-*` tab-pane и `/traffic-api/*`. Возврат legacy React SPA или повторное маппирование на Autolead-разделы запрещены.
