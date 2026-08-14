# БАГ-033: вкладки TrafficHub теряли свой навигационный контекст

## Симптом

Во встроенном разделе `TrafficHub` часть вкладок открывала нужный экран, но подсветка и hash-маршрутизация перескакивали в чужую ветку меню:

- `crm-settings` визуально превращался в общие `Настройки`;
- `crm-networks` подсвечивал `Autolead -> Офферы`;
- `crm-leads` и `crm overview` теряли контекст `TrafficHub`;
- при обновлении страницы по hash открывался не тот раздел меню.

## Зона системы

- `/root/TrafficHub/dashboard/app.js`
- `/root/TrafficHub/dashboard/index.html`

## Гипотеза

Один и тот же `tab-pane` используется несколькими ветками sidebar, но frontend выбирает активный пункт только по имени вкладки (`leads`, `offers`, `settings`, `messages`), а не по источнику перехода.

## Проверка

- Проверен live `dashboard/app.js`: старая логика использовала `LEGACY_HASH_TO_TAB` и после resolve теряла CRM-контекст.
- Проверен live `dashboard/index.html`: кнопки `TrafficHub` вызывали `switchTab(...)` напрямую, без отдельного CRM-route слоя.
- После фикса live `app.js` и HTML, отданные контейнером на `127.0.0.1:8080`, подтверждают наличие:
  - `HASH_ROUTES`
  - `openCrmSection(...)`
  - `data-crm-hash="crm-messages"`
  - owner-neutral route-group логики для `crm` и `autolead`.

## Наблюдение

Корневая проблема была не в backend и не в auth, а в маршрутизации frontend:

- `switchTab()` знал только конечный `tab-pane`;
- `TrafficHub` не сохранял `crm`-контекст при переходе;
- из-за этого один и тот же экран открывался, но nav state и hash принадлежали другой ветке меню.

## Вывод

Фикс сделан в общем UI-контуре:

- введён явный route-слой `HASH_ROUTES` вместо старого flat aliasing;
- добавлен `openCrmSection(...)`;
- `switchTab()` теперь принимает не только `tab`, но и `group/nav` контекст;
- `TrafficHub` и `Autolead` могут открывать общие `tab-pane` без потери правильной активной вкладки и hash.

Это общий frontend fix, он распространяется на всех текущих и будущих пользователей, потому что меняет один общий dashboard.

## Следующий шаг

Добавить отдельный frontend smoke/regression тест на hash-routing dashboard, чтобы `crm-settings`, `crm-networks`, `crm-leads` и `crm-messages` не откатывались к общим `settings/offers/leads/messages`.
