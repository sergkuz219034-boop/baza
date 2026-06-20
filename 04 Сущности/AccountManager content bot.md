# AccountManager content bot

## Назначение

Content bot в AccountManager управляет сбором/обработкой контента, целями публикации и задачами публикации в Telegram-каналы.

## Подтверждённые файлы

- `/root/TrafficHub/AccountManager/services/content_bot_service.py` — канонический сервис bot/runtime логики.
- `/root/TrafficHub/AccountManager/api/routers/content.py` — API для sources, targets, queued items, posting tasks и settings.
- `/root/TrafficHub/AccountManager/scheduler.py` — periodic jobs, включая polling Telegram updates.
- `/root/TrafficHub/AccountManager/dashboard/app.js` — dashboard controls для targets/tasks.

## Runtime

Контейнер: `traffichub_account_manager`.

Content bot polling работает через scheduler job `content-bot-updates`.

После исправления 2026-06-20:

- interval: 10 секунд;
- `max_instances=1`;
- `coalesce=True`;
- Telegram `409 Conflict` считается single-poller конфликтом, а не аварией процесса;
- `httpx` INFO-логирование отключено, чтобы bot token не попадал в логи.

## Ограничения

Telegram `getUpdates` допускает только одного активного poller для bot token. Если другой процесс или webhook уже владеет обновлениями, Telegram возвращает `409 Conflict`.

## Почему так

Scheduler не должен создавать параллельные poller instances: это повышает шанс Telegram conflict и засоряет логи. Поэтому polling ограничен одним экземпляром и более редким интервалом.

## Проверка

- `docker logs --since 30s traffichub_account_manager`
- `docker exec traffichub_account_manager grep -n content-bot-updates /app/scheduler.py`
- `docker exec traffichub_account_manager grep -n BotPollingConflict /app/services/content_bot_service.py`

## Связанные заметки

- [[2026-06-20 AccountManager content bot unfinished changes]]
- [[AccountManager Telegram polling conflict]]
