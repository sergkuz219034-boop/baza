# AccountManager Telegram polling conflict

## Проблема

Telegram `getUpdates` возвращал `409 Conflict`, а AccountManager писал traceback каждые 2 секунды. В логах также появлялся полный Telegram API URL с bot token.

## Контекст

`getUpdates` работает в single-consumer модели: один bot token не может одновременно обслуживаться несколькими poller-процессами или webhook и poller одновременно.

Фактический runtime до исправления:

- job `content-bot-updates` запускался каждые 2 секунды;
- было разрешено до 3 параллельных экземпляров;
- `httpx` писал INFO URL запросов.

## Решение

- Добавлен явный `BotPollingConflict` для `409 Conflict` на `getUpdates`.
- Конфликт логируется ограниченно и без traceback.
- Scheduler переведён на `seconds=10`, `max_instances=1`, `coalesce=True`.
- `httpx` INFO-логирование отключено в AccountManager.

## Последствия

- Логи перестают засоряться повторяющимися traceback.
- Bot token больше не попадает в свежие INFO-логи `httpx`.
- Если другой poller/webhook реально активен, content bot не будет получать updates до устранения второго владельца.

## Альтернативы

- Полностью перейти на webhook-mode и удалить polling job.
- Оставить polling, но добавить отдельный admin-флаг `content_bot_polling_enabled`.
- Использовать distributed lock, если появится несколько AccountManager replicas.

## Проверка

2026-06-20 на live-сервере:

- `traffichub_account_manager` пересобран и здоров;
- `tests/test_account_manager_access.py`, `tests/test_account_manager_content.py`, `tests/test_account_manager_import.py`: `9 passed`;
- за контрольное окно live-логов traceback/409-spam не повторился.
