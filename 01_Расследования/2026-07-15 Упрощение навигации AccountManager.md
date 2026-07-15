# 2026-07-15 Упрощение навигации AccountManager

## Симптом

В `AccountManager` существовали дублирующие экраны `Обзор` и `Аккаунты`, отдельные UI-вкладки очереди и общих настроек, а в `Подключениях` показывалась техническая форма импорта Telegram `StringSession`. Таблица аккаунтов дополнительно содержала ненужный столбец `Использование`.

## Зона системы

- `/root/TrafficHub/AccountManager/dashboard/index.html`
- `/root/TrafficHub/AccountManager/dashboard/app.js`
- `/root/TrafficHub/AccountManager/dashboard/js/telegram.js`
- `tests/test_account_manager_dashboard_simplification.py`

Связано с [[04_Код/Фронтенд]].

## Гипотеза

Экраны можно объединить без изменения backend API: `Обзор` использовал те же `accounts`, proxy и dashboard endpoints, а очередь, общие настройки и `StringSession` требовалось убрать только из пользовательского интерфейса.

## Проверка

- Сверены DOM-блоки, render-функции и обработчики событий.
- Подтверждено, что очередь контента, dashboard settings и `/api/telegram/import-session` остаются backend-контрактами.
- Добавлены DOM-regression тесты на состав вкладок, перенос блоков, таблицу из пяти столбцов и отсутствие лишних frontend-загрузок.
- Запущены `node --check` для `app.js` и `telegram.js`.
- В runtime-контейнере выполнены 10 целевых тестов: dashboard simplification, HR modal layout и AccountManager import.

## Наблюдение

- `Аккаунты` стали первой активной вкладкой.
- В неё перенесены сводка, карточки, фильтр платформ, обновление, массовая проверка, импорт Telegram, TG WS Proxy и proxy pool.
- `Обзор`, `Очередь контента`, общие `Настройки` и форма `StringSession` удалены из DOM.
- Backend API и данные не удалялись.
- Незавершённый Audience Parser был исключён из build-context через временный path-scoped stash и восстановлен после deploy.

## Вывод

Изменение зафиксировано product commit `49f9e7b99`. Все три GitHub workflow завершились успешно. `traffichub_account_manager` пересобран и имеет health `healthy`; внутри контейнера подтверждены активная вкладка `accounts`, отсутствие `overview` и формы `telegram-import-form`.

## Следующий шаг

При дальнейших изменениях навигации сохранять DOM-test как инвариант и не возвращать frontend-загрузки удалённых экранов без явного продуктового решения.
