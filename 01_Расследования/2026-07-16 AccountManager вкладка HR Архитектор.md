# AccountManager — вкладка HR Архитектор

## Симптом

Первый вариант ошибочно переименовал существующую вкладку `Telegram HR Agent` в `HR Архитектор`. Требование состояло в добавлении новой самостоятельной вкладки без удаления или переименования рабочего Telegram-контура.

## Зона системы

- `/root/TrafficHub/AccountManager/dashboard/index.html`
- `tests/test_account_manager_hr_architect_tab.py`
- существующий DOM/API-контракт `hr-agent`
- [[01_Расследования/2026-07-15 Telegram HR Agent и Business аккаунты]]

## Гипотеза

Новая вкладка должна иметь собственный frontend-контракт `hr-architect`, а существующий `hr-agent` должен оставаться без изменений. Пока отдельный backend-контракт не определён, безопасная реализация — независимый workspace без ложной привязки к Telegram HR API.

## Проверка

- По live-коду прослежены sidebar, `tab-hr-agent`, обработчик `refreshHrAgent()` и `/api/hr-agent/telegram/*`.
- Добавлен отдельный маршрут `data-tab="hr-architect"` и панель `id="tab-hr-architect"`.
- DOM-regression проверяет наличие двух разных sidebar-кнопок и двух разных панелей, а также сохранение controls Telegram HR Agent.
- Выполнены изолированные DOM assertions, `node --check` и `git diff --check`.

## Наблюдение

- Ошибочный product commit `c7ba86b57` переименовал существующий экран.
- Исправляющий commit `95dc95344` вернул `Telegram HR Agent` и добавил рядом самостоятельную вкладку `HR Архитектор`.
- `hr-agent` продолжает загружать ботов, вакансии и кандидатов; `hr-architect` не вызывает его API.
- GitHub CI, Extended project checks и Docker build завершились успешно.
- `account_manager` пересобран и пересоздан из server repo; контейнер `traffichub_account_manager` имеет статус `healthy`.
- В `/app/dashboard/index.html` runtime-контейнера одновременно подтверждены `Telegram HR Agent`, `HR Архитектор` и отдельная панель `tab-hr-architect`; публичный `https://am.traffic-hub.pro/api/health` вернул `{"status":"ok"}`.
- Незавершённые чужие изменения `.gitignore`, `AccountManager/api/routers/accounts.py` и `tests/test_account_manager_tdata_upload.py` были изолированы path-scoped stash на время build и полностью восстановлены.

## Вывод

`HR Архитектор` — отдельный frontend workspace. `Telegram HR Agent` остаётся самостоятельным рабочим экраном с прежним DOM/API-контрактом. Изменение доставлено на live без изменения backend и данных.

## Следующий шаг

При дальнейшем развитии сохранять один `hr-agent` DOM/API-контракт и расширять этот workspace, а не создавать параллельную HR-вкладку.
