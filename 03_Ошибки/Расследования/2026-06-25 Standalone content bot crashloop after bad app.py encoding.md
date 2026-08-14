# 2026-06-25 Standalone content bot crashloop after bad app.py encoding

## Симптом

- `@content34bot` перестал отвечать на `/start`.
- контейнер `traffichub_standalone_content_bot` был в состоянии restart loop.

## Зона системы

- live repo: `/root/TrafficHub`
- bot source: `/root/TrafficHub/standalone_content_bot/app.py`
- compose service: `standalone_content_bot`

## Гипотеза

- бот не отвечает не из-за Telegram polling, а потому что процесс `python app.py` падает на старте;
- вероятная причина: битая кодировка `app.py` в последнем образе.

## Проверка

- `docker compose ps` на live показал `traffichub_standalone_content_bot Restarting`.
- `docker logs traffichub_standalone_content_bot` показал:
  - `SyntaxError: Non-UTF-8 code starting with '\xd0' in file /app/app.py on line 865`
- серверный `/root/TrafficHub/standalone_content_bot/app.py` повторно проверен через `python3 -m py_compile`:
  - файл уже компилируется;
  - значит, crashloop был привязан к ранее собранному битому image-layer, а не к текущему checkout после восстановления файла.
- после `docker compose build --no-cache standalone_content_bot` и `docker compose up -d --force-recreate standalone_content_bot` контейнер поднялся нормально.
- startup-логи после пересоздания:
  - `Standalone content bot starting`
  - `Start polling`
  - `Run polling for bot @content34bot`
- Telegram Bot API подтвердил live-состояние:
  - `getMe` вернул bot id `8908175250`, username `content34bot`
  - `getWebhookInfo.url=""`, `pending_update_count=0`

## Наблюдение

- симптом "бот не отвечает" в этот раз был чистым следствием crashloop контейнера;
- polling и Telegram-token были исправны;
- корневая причина находилась в образе `standalone_content_bot`, собранном из битой версии `app.py`.

## Вывод

- для standalone content bot нужно считать обязательной проверку `python3 -m py_compile standalone_content_bot/app.py` перед rebuild;
- при жалобе "бот молчит" первым делом надо проверять `docker compose ps` и `docker logs`, а не только Telegram webhook/polling.

## Следующий шаг

- при следующих правках `standalone_content_bot/app.py` прогонять минимум:
  - `python3 -m py_compile standalone_content_bot/app.py`
  - `docker compose build standalone_content_bot`
  - `docker compose up -d --force-recreate standalone_content_bot`
  - `docker logs --tail 50 traffichub_standalone_content_bot`
