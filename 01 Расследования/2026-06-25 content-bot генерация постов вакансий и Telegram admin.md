# 2026-06-25 content-bot генерация постов вакансий и Telegram admin

## Симптом
Standalone `content-bot` был частично реализован: умел принять одну тему и сгенерировать вакансию, но не закрывал продуктовые требования по постам, HR-вакансиям, истории, пользователям и Telegram-админке.

## Зона системы
- Server repo: `/root/TrafficHub`
- Контейнер: `traffichub_standalone_content_bot`
- Код: `/root/TrafficHub/standalone_content_bot/app.py`
- Runtime DB: `/root/TrafficHub/standalone_content_bot/data/bot.sqlite3`, внутри контейнера `/data/bot.sqlite3`
- Compose service: `docker-compose.yml`, service `standalone_content_bot`

## Гипотеза
Для первой рабочей версии достаточно оставить текущий standalone-контур на `aiogram + SQLite + OpenRouter`, расширить `app.py` и не вводить отдельную web-админку до стабилизации Telegram UX.

## Проверка
Проверено на live-сервере:
- `docker ps` показывает `traffichub_standalone_content_bot Up`.
- `docker logs` после rebuild не содержит ошибок старта.
- `python -m py_compile /root/TrafficHub/standalone_content_bot/app.py` проходит.
- Внутри контейнера `import app` проходит.
- Зарегистрировано `18` message handlers и `4` callback handlers.
- В `.env` добавлен `ADMIN_IDS=7512871059`.
- Legacy `posts` мигрированы в новую таблицу `generations`.

## Наблюдение
До правки в БД была только legacy-таблица `posts`. Новая схема создала:
- `users`
- `generations`
- `prompts`
- `admin_actions`
- `access_rules`
- `events`

Старые `posts` оставлены для совместимости, но рабочая история теперь читается из `generations`.

## Вывод
`content-bot` переведён из single-purpose генератора вакансии в минимально рабочий Telegram-продукт:
- генерация Telegram-постов;
- генерация вакансий в режиме HR-архитектора;
- пошаговый UX;
- история генераций;
- профиль пользователя;
- Telegram-админка;
- блокировка/разблокировка пользователей;
- публикация черновика в целевой канал.

## Следующий шаг
Проверить живой UX руками в Telegram:
- `/start`
- `/post`
- `/vacancy`
- `/history`
- `/profile`
- `/admin`

Если продукт пойдёт в активное использование, следующий шаг — вынести `standalone_content_bot/app.py` в модули: `db.py`, `prompts.py`, `handlers/`, `services/ai.py`, `admin.py`.
