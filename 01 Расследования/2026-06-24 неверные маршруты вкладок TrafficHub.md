# Неверные маршруты вкладок TrafficHub

## Симптом

Пункты TrafficHub открывали страницы других разделов: «Партнёрские сети» открывали Autolead-офферы, несколько пунктов вели на одну вкладку.

## Зона системы

`dashboard/index.html`, `dashboard/app.js`, `/traffic/*`, native TrafficHub SPA.

## Гипотеза

После удаления отдельного frontend маршруты временно заменили алиасами на Autolead tabs.

## Проверка

- Проверена карта `HASH_ROUTES`.
- Проверена история `dashboard/traffic`.
- Проверены доступные backend endpoints `/traffic-api/*`.

## Наблюдение

- `crm` и `crm-leads` вели на `tab-leads`.
- `crm-messages` и `crm-messengers` вели на `tab-messages`.
- `crm-networks` вёл на Autolead `tab-offers`.
- Native SPA с маршрутами `/traffic/leads`, `/traffic/messengers`, `/traffic/funnels`, `/traffic/networks`, `/traffic/analytics`, `/traffic/finance`, `/traffic/settings` был удалён в `d45de271e`.

## Вывод

Native SPA восстановлен. `/traffic/*` снова обслуживает SPA и assets, а боковое меню направляет в собственные TrafficHub pages. Rabota.ru сообщения и вакансии оставлены в группе Autolead.

## Следующий шаг

Проверить переходы с пользовательской сессией после жёсткого обновления браузера.

Проверка: 8 SPA routes и asset отвечают `200`; auth regression `5 passed`. Код: `d4923ef94`.
