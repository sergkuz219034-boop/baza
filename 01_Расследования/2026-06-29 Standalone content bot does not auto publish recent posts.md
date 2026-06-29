# 2026-06-29 Standalone content bot does not auto publish recent posts

## Симптом

- пользователь сообщает, что `content bot` "не работает" и "не выкладывает посты".

## Зона системы

- live repo: `/root/TrafficHub`
- service: `standalone_content_bot`
- bot DB: `/root/TrafficHub/standalone_content_bot/data/bot.sqlite3`
- source integration: `Account Manager` internal Telethon API

## Гипотеза

- проблема не в падении контейнера и не в Telegram polling;
- последние посты останавливаются на стадии черновика (`draft`) и не доходят до публикации;
- автоматический scheduler publication может быть просто не настроен.

## Проверка

- `docker compose ps standalone_content_bot` на live показал `Up`.
- `docker logs traffichub_standalone_content_bot` показал нормальный polling и обработку свежих update.
- Bot API через runtime подтвердил, что целевой канал `@cadrypro_official` доступен:
  - `get_chat(@cadrypro_official)` успешен для bot token.
- В SQLite:
  - `settings.autopost_enabled = true`;
  - `list_scheduled_channels() = []`;
  - у существующих channel rows пустые `topic` и `schedule_times`;
  - значит scheduler-контур автопостинга сейчас фактически пуст.
- Последние события:
  - `source_post_generated` есть на `2026-06-28` и `2026-06-29`;
  - после них нет новых `draft_published`;
  - последние успешные `draft_published` были раньше.
- Последние `drafts` для пользователей `7512871059` и `934602871` существуют и содержат готовые тексты постов.

## Наблюдение

- бот сейчас работает по цепочке `source/channel -> messages -> AI -> draft`;
- публикация по recent source-flow не происходит автоматически;
- это соответствует UX-требованию "редактировать перед отправкой", а не аварии публикации;
- для настоящего автоматического выкладывания scheduler должен иметь хотя бы один channel с непустыми `topic` и `schedule_times` или `schedule_minutes`.

## Вывод

- на `2026-06-29` live `content bot` не сломан как сервис публикации;
- причина жалобы "не выкладывает посты" состоит из двух частей:
  - последние source-based посты остаются в `draft` и ждут ручного `✅ Опубликовать`;
  - автопостинг включён глобально, но для текущих channels scheduler не настроен, поэтому автоматически публиковать ему нечего.

## Следующий шаг

- если нужен ручной сценарий: проверить, что пользователь доходит до `draft_keyboard` и нажимает `✅ Опубликовать`;
- если нужен автоматический сценарий: заполнить channel `topic` и `schedule_times`, чтобы `list_scheduled_channels()` перестал быть пустым;
- если нужен отдельный UX для source-flow: явно пометить в интерфейсе, что после генерации создаётся черновик, а не мгновенная публикация.
