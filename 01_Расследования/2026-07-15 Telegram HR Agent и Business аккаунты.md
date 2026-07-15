# Telegram HR Agent и Business-аккаунты

## Симптом

`Telegram HR Agent` выглядит настроенным, но не автоматизирует личные чаты подключённых Telegram-аккаунтов.

## Зона системы

- `/root/TrafficHub/hr_ai_worker/main.py`
- `/root/TrafficHub/traffic_hub/hr_agent/service.py`
- `/root/TrafficHub/AccountManager/api/routers/hr_agent.py`
- таблицы `telegram_accounts`, `hr_agent_channel_bindings`, `hr_agent_candidates`, `hr_agent_messages`
- контейнеры `traffichub_app`, `traffichub_hr_ai_worker`
- [[05_Решения/Telegram Business сообщения обрабатываются через общий HR webhook]]

## Гипотеза

Бот исправен, но ни один Telegram Business-аккаунт не подключил его к личным чатам; отдельный Telethon-worker ошибочно воспринимается как основной runtime.

## Проверка

- Проверены live `getMe` и `getWebhookInfo` без вывода токена.
- Проверены подписанные update-типы, очередь и последняя ошибка webhook.
- Сверены код `hr_ai_worker`, AccountManager, HR webhook и фактические строки PostgreSQL.
- Добавлен regression-test на событие `business_connection`.
- Выполнены commit/push, GitHub checks, rebuild `autolead_bot`, public health и synthetic webhook smoke.

## Наблюдение

- `@Vectoria101_bot` валиден и имеет `can_connect_to_business=true`.
- Webhook указывает на `https://traffic-hub.pro/traffic-api/hr/webhooks/telegram`; очередь равна нулю, последней ошибки нет.
- Подписка включает `business_connection`, `business_message`, `edited_business_message`, `deleted_business_messages`.
- До фикса в `hr_agent_channel_bindings.extra_config` не сохранялись события подключения Business-аккаунта. Поэтому система не различала состояния «webhook исправен» и «аккаунт подключён».
- В live есть пять активных `telegram_accounts`, но `hr_ai_worker/main.py` ищет только Викторию, не расшифровывает AccountManager session и пишет HR-данные жёстко в `tenant_id=1`, `owner_username=admin`. Это legacy-прототип, не канон multi-account automation.
- Commit `39ec17913` сохраняет enabled/disabled Business connections в owner-scoped binding `extra_config.business_connections`.
- Regression: `tests/test_hr_agent_router.py`, `2 passed`; CI, Extended checks и Docker build успешны.
- После deploy `traffichub_app` healthy, `/api/health` возвращает `status=ok`, synthetic Business-event обработан новым кодом.

## Вывод

Канонический контур автоматизации личных чатов — Telegram Bot API Business webhook. Один HR-бот может получать отдельные `business_connection_id` от подключённых Business-аккаунтов и отвечать от имени соответствующего аккаунта. Серверная часть исправна и теперь фиксирует подключения. Ни одного реального Business connection на момент проверки не было; подключение каждого аккаунта подтверждается владельцем в Telegram и не может быть создано сервером без этого действия.

`hr_ai_worker` не является полноценной альтернативой и требует отдельного ADR/переработки либо удаления из production compose.

## Следующий шаг

На нужном Telegram-аккаунте открыть `Настройки → Telegram Business → Чат-боты`, подключить `@Vectoria101_bot`, разрешить управление личными чатами и отправить тестовое входящее сообщение с другого аккаунта. После update `business_connection` проверить `extra_config.business_connections`, создание owner-scoped кандидата и исходящий ответ с тем же `business_connection_id`.

## Связанные заметки

- [[05_Решения/Telegram Business сообщения обрабатываются через общий HR webhook]]
- [[05_Решения/Telegram HR бот подключается по названию и токену]]
- [[05_Эксплуатация/Развёртывание]]
