# 2026-06-23 Standalone content bot cleanup

## Симптом

- `contentbot` уже вынесен в отдельный сервис `standalone_content_bot`, но в `AccountManager` оставались:
- scheduler job `content-bot-updates`;
- private-chat polling через `getUpdates`;
- API endpoints `/api/content/bot-config`, `/api/content/bot-status`, `/api/content/bot-generate`;
- UI-вкладка админки, которая продолжала дергать удалённые bot-endpoints.

## Зона системы

- live repo: `/root/TrafficHub`
- legacy code:
  - `AccountManager/services/content_bot_service.py`
  - `AccountManager/scheduler.py`
  - `AccountManager/api/routers/content.py`
  - `AccountManager/dashboard/app.js`
  - `AccountManager/dashboard/index.html`
- active standalone service:
  - `standalone_content_bot/app.py`
  - compose service `standalone_content_bot`

## Гипотеза

- После выноса бота в отдельный контейнер старый bot-contour в `AccountManager` стал лишним и создавал двойную ответственность:
- два места для bot UX/config;
- риск ложных 404/битой админки;
- лишний scheduler polling внутри `AccountManager`.

## Проверка

- На live по коду и grep подтверждено наличие `poll_bot_updates`, `content-bot-updates` и `/api/content/bot-*`.
- После удаления legacy-фрагментов `AccountManager` пересобран и поднят заново.
- По startup-логам `AccountManager` после перезапуска зарегистрированы только:
  - `_run_google_checks`
  - `_run_telegram_checks`
  - `_run_social_checks`
  - `_run_content_tasks`

## Наблюдение

- Job `content-bot-updates` больше не регистрируется.
- В `AccountManager/dashboard/*` больше нет вызовов `/api/content/bot-config`.
- Вкладка `Контент-бот` удалена из админки; standalone bot пока не интегрирован в `AccountManager`.
- Контейнер `traffichub_account_manager` после пересборки поднялся healthy.
- `traffichub_standalone_content_bot` продолжает работать отдельно.
- Runtime-секреты standalone bot (`.env`) и SQLite (`data/bot.sqlite3`) остаются вне Git; для build context добавлен `standalone_content_bot/.dockerignore`.
- В `standalone_content_bot/app.py` добавлена очистка Telegram HTML: `<br>` заменяется на перевод строки, неподдерживаемые теги удаляются перед предпросмотром и публикацией.

## Вывод

- На live подтверждён новый канон: Telegram `contentbot` обслуживается standalone сервисом, а не `AccountManager`.
- `AccountManager` очищен от legacy polling/API/UI-контура старого бота.
- Runtime-risk `TelegramBadRequest: Unsupported start tag "br"` закрыт sanitation-слоем в standalone bot.

## Следующий шаг

- Отдельно решить, нужна ли новая read-only ссылка из `AccountManager` на standalone bot status, или интеграция пока должна отсутствовать полностью.
