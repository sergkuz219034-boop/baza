# 2026-06-25 TrafficHub UI overview removal and admin table polish

## Симптом

После удаления вкладки `Обзор` внутри TrafficHub CRM краснел GitHub Actions `CI`, а админская таблица визуально могла выходить за ширину экрана.

## Зона системы

- Frontend: `/root/TrafficHub/dashboard/index.html`
- Frontend logic: `/root/TrafficHub/dashboard/app.js`
- Styles: `/root/TrafficHub/dashboard/style.css`
- Tests: `/root/TrafficHub/tests/test_traffic_embedded_auth.py`
- Runtime container: `traffichub_app`

## Гипотеза

Тест маршрутов TrafficHub остался привязан к старой вкладке `crm-overview`, а CSS админской таблицы требовал дополнительного ограничения горизонтального overflow и минимальных hit-area для кнопок.

## Проверка

- `node --check dashboard/app.js`
- `git diff --check`
- `docker compose up -d --build autolead_bot`
- `docker compose exec -T autolead_bot python -m pytest -q`
- `curl -fsS http://127.0.0.1:8080/api/health`
- GitHub Actions check-suites для commit `1a0c71366`

## Наблюдение

- Корневой маршрут TrafficHub теперь ведёт на `crm-leads`, а не на удалённый `crm-overview`.
- В `dashboard/index.html` нет `tab-crm-overview` и кнопки `Обзор` в подменю TrafficHub.
- `/traffic` отдаёт redirect на `/#crm-leads`.
- В контейнере прошёл полный набор тестов: `333 passed, 43 skipped`.
- GitHub Actions для HEAD завершились `success` после задержки создания run.

## Вывод

Подтверждённый канон UI: у TrafficHub CRM больше нет отдельного раздела `Обзор`; входная точка открывает `Лиды`. Админская таблица должна укладываться в страницу без отдельного горизонтального скролла, а кнопки управления аккаунтами должны сохранять минимум `40px` hit-area.

## Следующий шаг

- При любых следующих изменениях TrafficHub-навигации обновлять одновременно `HASH_ROUTES`, `TAB_HASH`, `TABS`, HTML-панели и тесты маршрутов.
- Для визуальных правок проверять не только скриншот, но и DOM-инварианты: отсутствие `crm-overview`, отсутствие `transition: all`, отсутствие document horizontal overflow.

