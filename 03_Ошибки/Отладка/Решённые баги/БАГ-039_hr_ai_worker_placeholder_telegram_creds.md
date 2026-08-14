# БАГ-039: hr_ai_worker не отвечал из-за заглушек Telegram credentials

## Симптом

`hr_ai_worker` не отвечал на входящие сообщения и падал сразу после запуска.

## Зона системы

- `hr_ai_worker/main.py`
- `telegram_accounts`
- live `.env`

## Гипотеза

После дублирования Telegram session worker пытается перейти на bot-token, но берёт `api_id/api_hash` из БД-заглушек `12345 / hash`, а не из реальных Telegram переменных окружения.

## Проверка

- В логах контейнера было:
  - `AuthKeyDuplicatedError`
  - затем `ApiIdInvalidError`
- В `telegram_accounts` лежали:
  - `api_id=12345`
  - `api_hash=hash`
  - `session_string` присутствовал
- В `.env` live репозитория есть корректные:
  - `TELEGRAM_API_ID`
  - `TELEGRAM_API_HASH`
  - `TELEGRAM_BOT_TOKEN`
- После правки `hr_ai_worker/main.py` worker стартовал и дошёл до `HR AI Telegram Client started.` без ошибки авторизации.

## Наблюдение

Проблема была не в OpenAI-части и не в handler'е сообщений. Worker ломался до начала обработки входящих сообщений на этапе Telegram bootstrap.

## Вывод

Для `hr_ai_worker` источником истины по Telegram credentials должны быть live env-переменные. Значения из `telegram_accounts` годятся только как data row для session string, но не как валидные credentials.

## Следующий шаг

- Не возвращать fallback на `12345/hash`.
- При следующем регрессе первым делом проверять контейнерный лог и содержимое `telegram_accounts`.
