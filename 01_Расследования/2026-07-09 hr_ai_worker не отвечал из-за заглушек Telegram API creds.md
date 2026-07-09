# 2026-07-09 hr_ai_worker не отвечал из-за заглушек Telegram API creds

## Симптом

`hr_ai_worker` не отвечал и падал при старте. В live логах был сначала `AuthKeyDuplicatedError`, затем ретрай в bot-mode заканчивался `ApiIdInvalidError`.

## Зона системы

- live worker: `/root/TrafficHub/hr_ai_worker/main.py`
- compose service: `hr_ai_worker`
- Telegram bootstrap credentials
- БД: `telegram_accounts`

## Гипотеза

Worker брал `api_id/api_hash` из `telegram_accounts`, где лежали заглушки `12345 / hash`, а не реальные Telegram credentials из `.env`. Из-за этого попытка переключиться на bot-token после дублированной user-session ломалась на `ImportBotAuthorizationRequest`.

## Проверка

- `docker ps -a` показывал `traffichub_hr_ai_worker` в состоянии `Exited (1)`.
- `docker logs traffichub_hr_ai_worker` показывал:
  - `AuthKeyDuplicatedError`
  - затем `ApiIdInvalidError: The api_id/api_hash combination is invalid`
- В PostgreSQL запись `telegram_accounts` содержала:
  - `api_id=12345`
  - `api_hash=hash`
  - `session_string` длиной 353 символа
- В `.env` live репозитория есть реальные значения:
  - `TELEGRAM_API_ID`
  - `TELEGRAM_API_HASH`
  - `TELEGRAM_BOT_TOKEN`

## Наблюдение

- `hr_ai_worker/main.py` сначала строил `TelegramClient` из `session_string`, но `api_id/api_hash` брал из строки БД без валидации.
- При `AuthKeyDuplicatedError` worker пытался повторно стартовать как bot, но использовал те же неверные credentials из БД.
- После замены логики на приоритет `TELEGRAM_API_ID/TELEGRAM_API_HASH` worker поднялся и в логах дошёл до `HR AI Telegram Client started.`

## Вывод

Причина не в самом Telegram worker loop, а в источнике credentials:

- session string в БД валидна как строка;
- `api_id/api_hash` в БД являются заглушками;
- для ретрая и обычного старта нужны реальные env credentials.

## Следующий шаг

- Держать приоритет `TELEGRAM_API_ID/TELEGRAM_API_HASH` выше БД-заглушек.
- Если `AuthKeyDuplicatedError` повторится, проверять, не используется ли та же session string ещё где-то одновременно.
- Для похожих инцидентов сначала смотреть `telegram_accounts` и live `.env`, а не только runtime лог.
