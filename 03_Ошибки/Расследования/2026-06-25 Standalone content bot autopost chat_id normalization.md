# 2026-06-25 Standalone content bot autopost chat_id normalization

## Симптом

- автопостинг падал с `TelegramBadRequest: chat not found`;
- ручная публикация из черновика падала той же ошибкой.

## Зона системы

- live repo: `/root/TrafficHub`
- bot source: `/root/TrafficHub/standalone_content_bot/app.py`
- runtime DB: `/data/bot.sqlite3`
- таблица `channels`

## Гипотеза

- в `channels.chat_id` сохранён не Telegram `chat_id`, а URL канала `https://t.me/...`;
- Bot API принимает только `@username` или numeric chat id вида `-100...`.

## Проверка

- в live SQLite для активного канала было сохранено:
  - `chat_id = https://t.me/cadrypro_official`
- `getChat(chat_id=https://t.me/cadrypro_official)` возвращал `400 Bad Request`;
- `getChat(chat_id=@cadrypro_official)` возвращал корректный channel object;
- `getChatMember(chat_id=@cadrypro_official, user_id=8908175250)` подтвердил:
  - bot status `administrator`
  - `can_post_messages=true`
- технический send/delete test через Bot API прошёл успешно.

## Наблюдение

- корень ошибки был не в правах бота и не в расписании;
- проблема возникала из-за отсутствия нормализации `t.me/... -> @username` при сохранении канала;
- из-за этого ошибка проявлялась поздно, уже в момент отправки поста.

## Вывод

- standalone bot должен нормализовать channel reference при сохранении и перед публикацией;
- при добавлении канала бот должен валидировать его через `getChat`, чтобы не сохранять битый `chat_id`.

## Следующий шаг

- держать в коде оба защитных слоя:
  - нормализация `https://t.me/...`, `t.me/...`, `username` -> `@username`;
  - live-проверка канала через Bot API перед сохранением.
