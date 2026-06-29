# 2026-06-30 Rabota вакансии перенесены в TrafficHub меню

## Симптом

- Пользователь попросил перенести вкладку `Вакансии Rabota.ru` из меню `Autolead` во вкладку `TrafficHub`.

## Зона системы

- Frontend dashboard:
  - `/root/TrafficHub/dashboard/index.html`;
  - `/root/TrafficHub/dashboard/app.js`;
  - `/root/TrafficHub/tests/test_traffic_embedded_auth.py`.

## Гипотеза

- Это UI-навигационная проблема: экран вакансий можно оставить на существующем `tab=vacancies`, но кнопку и route group надо перевести в `TrafficHub`.

## Проверка

- Проверено в live repo `/root/TrafficHub`.
- `data-autolead-tab="vacancies"` удалён из Autolead subnav.
- Добавлена кнопка `data-crm-hash="vacancies"` с `openCrmSection('vacancies')` в TrafficHub subnav.
- `HASH_ROUTES.vacancies` переведён в `group: 'crm'`.

## Наблюдение

- Экран продолжает использовать legacy tab id `vacancies` и API `/api/offers/vacancies`.
- Это минимальный безопасный перенос без изменения бизнес-логики загрузки вакансий.

## Вывод

- Каноническое место вкладки `Вакансии Rabota.ru` в UI: меню `TrafficHub`.
- Regression закреплён тестом `test_rabota_vacancies_live_under_traffic_menu`.
- Product commit: `ec4aa8c16`.

## Следующий шаг

- Если позже потребуется полное переименование route, делать отдельной задачей с проверкой всех deep links `#vacancies`.
