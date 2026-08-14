# AccountManager — вкладка HR Архитектор

## Симптом

Первый вариант ошибочно переименовал существующую вкладку `Telegram HR Agent` в `HR Архитектор`. Требование состояло в добавлении новой самостоятельной вкладки без удаления или переименования рабочего Telegram-контура.

## Зона системы

- `/root/TrafficHub/AccountManager/dashboard/index.html`
- `tests/test_account_manager_hr_architect_tab.py`
- существующий DOM/API-контракт `hr-agent`
- [[03_Ошибки/Расследования/2026-07-15 Telegram HR Agent и Business аккаунты]]

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

## Генерация креативов через OpenRouter

### Симптом

Отдельная вкладка `HR Архитектор` была только пустым workspace и не выполняла прикладную задачу.

### Проверка

- Добавлен независимый endpoint `POST /api/hr-architect/generate` в `AccountManager/api/routers/hr_architect.py`.
- Ключ читается только из `OPENROUTER_API_KEY` внутри контейнера; браузер его не получает.
- Вход ограничен Pydantic-контрактом: вакансия, аудитория, подтверждённые условия, канал, тон, цель и 1–5 вариантов.
- OpenRouter обязан вернуть JSON с `title`, `text`, `cta`, `short_text`; невалидный или пустой ответ преобразуется в контролируемый `502`.
- Выполнены mocked endpoint smoke, DOM/API assertions, GitHub CI, Extended checks и Docker build.
- После deploy выполнена реальная генерация одного непубликуемого тестового креатива через `openai/gpt-4.1-mini`.

### Наблюдение

- UI поддерживает Telegram, VK, Avito, hh.ru и универсальный формат; четыре тона и до пяти вариантов.
- Результаты отображаются карточками и копируются без сохранения в БД.
- Модель настраивается через `HR_ARCHITECT_OPENROUTER_MODEL`, default — `openai/gpt-4.1-mini`.
- Product commit: `17bb3167f`; контейнер `traffichub_account_manager` healthy, public health — `status=ok`.
- Deploy image собран из committed `HEAD:AccountManager`, поэтому незавершённый merge `deploy/Caddyfile` и чужие Account Manager changes не попали в image.

### Вывод

`HR Архитектор` стал отдельным owner-authenticated генератором текстовых HR-креативов через серверный OpenRouter-контур. Он не меняет и не использует runtime Telegram HR Agent.

### Следующий шаг

Если потребуется история и повторное использование, добавить owner-scoped таблицу креативов; текущая версия намеренно не сохраняет введённые данные и результаты.
