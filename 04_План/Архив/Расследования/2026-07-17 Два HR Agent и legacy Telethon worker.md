# 2026-07-17 Два HR Agent и legacy Telethon worker

## Симптом

Пользователь наблюдал два HR Agent. Требовался один агент, который отвечает через OpenRouter, при сохранении Telethon-входа Виктории для парсинга AccountManager.

## Зона системы

- `docker-compose.yml`
- `hr_ai_worker/main.py` до product commit `fd392b408`
- `traffic_hub/hr_agent/service.py`
- таблицы `hr_agent_channel_bindings`, `hr_agent_configs`, `hr_agent_touches`
- `AccountManager/services/content_parser.py` и server-side tdata

## Гипотеза

Новый Telegram Business webhook и старый Telethon worker могли независимо отвечать в одни и те же чаты.

## Проверка

- Проверены live-контейнеры, процессы и Compose.
- Проверены binding, Business connection, LLM config и очередь касаний в PostgreSQL.
- Проверены `getWebhookInfo`, модель исходящих сообщений и логи legacy worker.
- Проверены Telethon runtime и tdata AccountManager без удаления или повторной авторизации сессий.

## Наблюдение

- В БД активен один binding `HR Виктория` и одна Business connection `@JobVictory` через `@Vectoria101_bot`.
- Каноническая модель — OpenRouter `openai/gpt-4.1-mini`, `llm_enabled=true`.
- Касания настроены через 24 и 72 часа; их текст формирует тот же OpenRouter-контур.
- Одновременно в Compose существовал `traffichub_hr_ai_worker`: отдельный Telethon `events.NewMessage` listener с собственной генерацией `openrouter/free`.
- На момент проверки worker не нашёл строку Виктории в `telegram_accounts` и был idle, но оставался отдельным потенциальным writer после появления session string.
- AccountManager содержит Telethon `1.44.0` и server-side tdata, включая каталог Виктории. Эти данные нужны парсеру и не относятся к Business-ответам.

## Вывод

Архитектура допускала два независимых HR writer. Legacy worker удалён из кода, Compose, deploy allowlist и CI в product commit `fd392b408`; live-контейнер остановлен и удалён. Единственный writer — общий Telegram Business webhook с OpenRouter.

Telethon AccountManager не удалён: он остаётся transport-слоем чтения чатов, каналов и переписок. Он не должен подписываться на входящие для HR-ответов.

## Следующий шаг

- При восстановлении записей Telegram-аккаунтов в UI привязать существующий tdata Виктории к owner-scoped AccountManager account, не копируя session string в отдельный HR worker.
- Для проверки дублей контролировать: один active binding, одна enabled Business connection и отсутствие контейнера `traffichub_hr_ai_worker`.

Связано: [[99_Архив/Решения/Telegram Business сообщения обрабатываются через общий HR webhook]], [[99_Архив/Старые сущности/AccountManager content bot]], [[02_Код/Архитектура/Карта контейнеров и модулей]]
