# 2026-06-20 AccountManager content bot unfinished changes

## Симптом

В `/root/TrafficHub` остался незавершённый блок изменений AccountManager. Live-контейнер `traffichub_account_manager` дополнительно сыпал traceback по Telegram `getUpdates` `409 Conflict` каждые 2 секунды.

## Зона системы

- `AccountManager/services/content_bot_service.py`
- `AccountManager/scheduler.py`
- `AccountManager/api/routers/content.py`
- `AccountManager/dashboard/app.js`
- контейнер `traffichub_account_manager`

## Гипотеза

Старые изменения относятся к реальному content-bot функционалу и должны быть применены, но live runtime не был пересобран. Отдельно Telegram poller конфликтует с другим poller/webhook и должен обрабатываться как ожидаемый single-owner конфликт, а не как аварийный traceback.

## Проверка

- Проверен `git status` в `/root/TrafficHub`.
- Проверены AccountManager diffs.
- Запущены AccountManager tests в `autolead_server_bot`.
- Пересобран и перезапущен `account_manager`.
- Проверены live-логи `traffichub_account_manager` после restart.
- Проверен поиск Telegram bot-token паттернов в `/app/data/logs` и `/app/data/*.log*`.

## Наблюдение

- Незавершённые изменения затрагивали content sources/targets/task reuse, default posting target, dashboard controls и Telegram content bot.
- Дублирующий `AccountManager/content_bot_service.py` не являлся каноническим импортом; канонический файл находится в `AccountManager/services/content_bot_service.py`.
- Старый runtime опрашивал Telegram каждые 2 секунды с `max_instances=3`, что усиливало конфликт `getUpdates`.
- `httpx` INFO-логирование выводило полный Telegram API URL, включая bot token.

## Вывод

Исправления применены на сервере и отправлены в GitHub коммитом `1a9462b04`.

- `poll_bot_updates()` теперь перехватывает Telegram `409 Conflict` как `BotPollingConflict` и не пишет traceback при каждом цикле.
- Scheduler content-bot polling переведён на `seconds=10`, `max_instances=1`, `coalesce=True`.
- `httpx` INFO-логирование в AccountManager отключено.
- Старые токены в runtime-логах отредактированы.
- Дублирующий root-level content bot service перенесён в backup-архив вне repo.
- AccountManager tests проходят: `9 passed`.

## Следующий шаг

- Если Telegram bot должен работать через polling, убедиться, что нет другого процесса или webhook на тот же bot token.
- Если нужен webhook-mode, явно задокументировать owner процесса и отключить polling job.

## Связанные заметки

- [[AccountManager content bot]]
- [[AccountManager Telegram polling conflict]]
