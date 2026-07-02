# 2026-07-02 Standalone content bot publishes to wrong active channel

## Симптом

- Пользователь сообщает, что `content bot` публикует посты не в том канале, который выбран как активный.

## Зона системы

- live repo: `/root/TrafficHub`
- service: `standalone_content_bot`
- runtime DB: `/root/TrafficHub/standalone_content_bot/data/bot.sqlite3`
- code: `/root/TrafficHub/standalone_content_bot/app.py`

## Гипотеза

- проблема не в Telegram Bot API и не в `publish_draft()` как таковом;
- owner-scoped модель каналов нарушена на уровне SQLite schema и `add_channel()`;
- из-за этого `active_channel_id:<user_id>` может указывать на строку `channels`, которая уже принадлежит другому пользователю.

## Проверка

- В live `settings` были значения:
  - `active_channel_id:7512871059 = 26`
  - `active_channel_id:934602871 = 26`
- При этом в `channels` строка `id = 26` принадлежала только `user_id = 934602871`.
- `channels` имела глобальный unique по `chat_id`, а не owner-scoped unique:
  - schema: `chat_id TEXT NOT NULL UNIQUE`
  - `add_channel()` использовал `ON CONFLICT(chat_id) DO UPDATE SET user_id=excluded.user_id`
- Значит добавление одного и того же `@username` другим пользователем физически переносило row к новому owner.
- `resolve_active_channel(user_id)` берёт каналы только через `list_channels(user_id)`. Если `active_channel_id` указывает на чужую строку, функция возвращает `None` и публикация падает в fallback `SETTINGS.target_chat_id`.

## Наблюдение

- root cause не в polling и не в выборе канала через UI, а в сломанной data model:
  - `active_channel_id` хранится user-scoped;
  - `channels.chat_id` был уникален глобально;
  - `add_channel()` нарушал ownership при upsert.
- Это системно ломало оба контура:
  - ручную публикацию черновиков;
  - дальнейшую работу с активным каналом в админке.

## Вывод

- Баг подтверждён как schema/runtime defect.
- Исправление на live:
  - `channels` мигрирован с `UNIQUE(chat_id)` на `UNIQUE(user_id, chat_id)`;
  - `add_channel()` переведён на `ON CONFLICT(user_id, chat_id)`;
  - `resolve_active_channel()` теперь сбрасывает битый `active_channel_id`, если он не принадлежит текущему owner;
  - `set_active_channel()` валидирует, что канал принадлежит текущему пользователю.
- Дополнительно восстановлены live-данные:
  - для `7512871059` создана owner-scoped строка `channels.id = 29` с `chat_id = @cadrypro_official`;
  - `active_channel_id:7512871059` переведён с `26` на `29`.

## Следующий шаг

- Проверить руками в Telegram сценарий:
  - выбрать канал;
  - сгенерировать черновик;
  - нажать `✅ Опубликовать`;
  - убедиться, что сообщение уходит именно в owner-scoped активный канал.
- Если снова появятся жалобы на "не тот канал", сначала проверять:
  - `settings.active_channel_id:<user_id>`;
  - owner строки в `channels`;
  - fallback-публикации в `generations.target_chat_id`.
