# AccountManager — вкладка HR Архитектор

## Симптом

В sidebar Account Manager рабочий HR-контур назывался `Telegram HR Agent`, тогда как продуктовая роль экрана — настройка HR-ботов, вакансий и воронки кандидатов.

## Зона системы

- `/root/TrafficHub/AccountManager/dashboard/index.html`
- `tests/test_account_manager_hr_architect_tab.py`
- существующий DOM/API-контракт `hr-agent`
- [[01_Расследования/2026-07-15 Telegram HR Agent и Business аккаунты]]

## Гипотеза

Для вкладки «HR Архитектор» не нужен второй экран: существующая панель `data-tab="hr-agent"` уже объединяет Telegram-ботов, каталог офферов и кандидатов. Дублирование навигации создало бы две точки входа к одному owner-scoped backend-контуру.

## Проверка

- По live-коду прослежены sidebar, `tab-hr-agent`, обработчик `refreshHrAgent()` и `/api/hr-agent/telegram/*`.
- Подтверждено, что изменение ограничено UI-текстом и не меняет идентификаторы, API или данные.
- Добавлен DOM-regression на единственную sidebar-кнопку, заголовок и сохранение ключевых элементов панели.
- Выполнены изолированные DOM assertions, `node --check` и `git diff --check`.

## Наблюдение

- Sidebar и заголовок экрана переименованы в `HR Архитектор`.
- Описание экрана теперь явно перечисляет HR-ботов, вакансии и воронку кандидатов.
- Внутренний идентификатор `hr-agent` сохранён ради обратной совместимости frontend и API.
- Product commit: `c7ba86b57`.
- GitHub CI, Extended project checks и Docker build завершились успешно.
- `account_manager` пересобран и пересоздан из server repo; контейнер `traffichub_account_manager` имеет статус `healthy`.
- В `/app/dashboard/index.html` runtime-контейнера подтверждены sidebar и заголовок `HR Архитектор`; публичный `https://am.traffic-hub.pro/api/health` вернул `{"status":"ok"}`.
- Незавершённые чужие изменения `.gitignore`, `AccountManager/api/routers/accounts.py` и `tests/test_account_manager_tdata_upload.py` были изолированы path-scoped stash на время build и полностью восстановлены.

## Вывод

«HR Архитектор» является новым продуктовым названием существующего HR Agent workspace, а не отдельной дублирующей подсистемой. Изменение доставлено на live без изменения backend и данных.

## Следующий шаг

При дальнейшем развитии сохранять один `hr-agent` DOM/API-контракт и расширять этот workspace, а не создавать параллельную HR-вкладку.
