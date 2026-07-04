# Content Bot

## Назначение
`content-bot` — standalone Telegram-бот в составе TrafficHub, который генерирует контент-посты и вакансии, хранит историю генераций и даёт минимальную админку прямо в Telegram.

## Подтверждённые runtime-факты
- Рабочий код: `/root/TrafficHub/standalone_content_bot/app.py`.
- Контейнер: `traffichub_standalone_content_bot`.
- Docker service: `standalone_content_bot`.
- Runtime DB: `/data/bot.sqlite3` внутри контейнера.
- Host DB path: `/root/TrafficHub/standalone_content_bot/data/bot.sqlite3`.
- Framework: `aiogram`.
- HTTP-клиент AI: `httpx`.
- DB layer: `aiosqlite`.
- AI provider: `OpenRouter`, env `OPENROUTER_API_KEY`, model `OPENROUTER_MODEL`.
- Target channel по умолчанию берётся из `TARGET_CHAT_ID`.
- С `3fd3f611b` каналы публикации user-scoped: таблица `channels` имеет `user_id`, активный канал хранится ключом `active_channel_id:<telegram_user_id>`.
- Автопостинг настраивается отдельно от добавления канала: канал добавляется по `@username`/`-100...`, тематика и часы задаются через меню `⚡ Автопостинг`.
- С `95c39bd6a` все публикации постов отправляются с обязательной inline-кнопкой:
  - текст по умолчанию: `Перейти на сайт`;
  - ссылка по умолчанию: `https://hrcadry.pro`;
  - переопределяется env `CONTENT_BOT_CTA_TEXT` и `CONTENT_BOT_CTA_URL`.
- С `4d07384c4` текст поста перед публикацией дополнительно очищается от плейсхолдеров ссылок (`[вставьте ссылку]`, `[ваша ссылка]`, `ваша_ссылка_здесь`, `example.com`). Ссылка должна жить в inline-кнопке, а не в теле поста.

## Команды
- `/start` — старт и главное меню.
- `/help` — список команд.
- `/post` — пошаговая генерация Telegram-поста.
- `/vacancy` — пошаговая генерация вакансии в режиме HR-архитектора.
- `/history` — последние генерации текущего пользователя.
- `/profile` — профиль, роль, счётчики.
- `/admin` и `/stats` — Telegram-админка для `ADMIN_IDS`.
- `/block TELEGRAM_ID` — заблокировать пользователя.
- `/unblock TELEGRAM_ID` — разблокировать пользователя.

## Таблицы SQLite
- `users` — Telegram users, статус, роль, счётчики, first/last activity.
- `user_state` — текущий шаг пошагового сценария.
- `drafts` — последний черновик пользователя перед публикацией.
- `generations` — история постов и вакансий.
- `prompts` — место для будущего хранения редактируемых промптов.
- `admin_actions` — аудит действий администратора.
- `access_rules` — задел под лимиты и тарифы.
- `events` — технические события бота.
- `posts` — legacy-таблица, оставлена для совместимости.
- `channels` — каналы публикации, owner-scoped по `user_id`, с полями `topic`, `schedule_times`, `schedule_minutes`.

## Почему пока standalone
Текущий TrafficHub уже перегружен Autolead/AccountManager/CRM-контурами. Для content-bot выбран отдельный контейнер и SQLite, чтобы не смешивать Telegram polling и основной web-runtime. Это снижает риск регрессий в TrafficHub.

## Ограничения
- Web-админка пока не реализована как отдельный интерфейс; минимальная админка находится в Telegram.
- `app.py` стал крупным файлом. Это допустимо для быстрого восстановления продукта, но требует последующего split.
- AI-ключ OpenRouter остаётся обязательным для полноценной генерации. Если ключ пустой, бот выдаёт fallback-шаблон.
- Глобальный toggle автопостинга остаётся общим, но выбор активного канала уже user-scoped.
- Если у активного канала пустые `topic` и `schedule_times`, планировщик не публикует посты даже при включённом глобальном `autopost_enabled`.
- Очистка ссылочных плейсхолдеров является защитным слоем после LLM. Промпт всё равно запрещает писать URL/placeholder в тексте, но runtime-фильтр нужен, потому что модель может нарушить инструкцию.

## Связанные заметки
- [[2026-06-25 content-bot генерация постов вакансий и Telegram admin]]
- [[Content Bot deploy and debug]]
## Миграции SQLite
`CREATE TABLE IF NOT EXISTS` не обновляет существующие таблицы. Для изменений схемы используется idempotent helper `_ensure_column()` в `standalone_content_bot/app.py`. Это обязательно для live-БД `/data/bot.sqlite3`, где уже есть legacy-таблицы.

См. [[2026-06-25 content-bot кнопки не работают после расширения]].
