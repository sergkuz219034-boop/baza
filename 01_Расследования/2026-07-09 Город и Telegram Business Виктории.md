# Город и Telegram Business Виктории

## Симптом

1. HR-бот повторно спрашивал город после ответов `москва`, `Москва`, `Челяба`.
2. Бот, подключённый в Telegram через «Автоматизацию чатов» аккаунта Виктории, не отвечал в личных чатах.
3. После включения Business update ответ на сообщение из чата Виктории ушёл от имени самого бота, а не от имени аккаунта Виктории.

## Зона системы

- `traffic_hub/hr_agent/service.py`
- `traffic_hub/api/routers/hr_agent.py`
- `AccountManager/api/routers/hr_agent.py`
- таблицы `hr_agent_candidates`, `hr_agent_conversations`, `hr_agent_messages`
- Telegram Bot API Business updates

## Гипотеза

- Парсер города распознаёт только фразы с префиксом.
- Автоматизация аккаунта требует отдельной обработки Telegram Business updates.

## Проверка

- В БД подтверждены три входящих ответа с городами при пустых `city` и `answered_fields`.
- `_extract_profile` принимал город только после `город`, `из города`, `живу в`, `нахожусь в`.
- Worker Виктории получил `AuthKeyDuplicatedError` пользовательской сессии и перешёл в режим обычного бота.
- Основной webhook разбирал только `message`/`edited_message`, но не `business_message`.
- Добавлены тесты контекстного ответа города и Business delivery.
- 2026-07-09 21:32 live runtime подтвердил `business_message` от пользователя `934602871`: сообщение пришло через Business-контур, но `sendMessage` ушёл без `business_connection_id`, потому что `parse_channel_payload()` читал идентификатор с верхнего уровня update.

## Наблюдение

Telegram Business передаёт сообщение в `business_message` и требует тот же `business_connection_id` в исходящем `sendMessage`. Это отдельный транспортный режим, даже если используется тот же bot token.

## Вывод

- Однословный город сохраняется как ответ на последний вопрос `city`.
- Webhook принимает `business_message` и `edited_business_message`.
- `business_connection_id` сохраняется в состоянии кандидата и используется для ответов и follow-up.
- `setWebhook` явно включает Business update-типы.
- Для Telegram Bot API `business_connection_id` нужно читать из `business_message.business_connection_id`; верхнеуровневый fallback оставлен только для совместимости с тестовыми/legacy payload.
- Тесты проходят; commits `4504e99c0`, `9636fc4e8`, `3560f5bda`; live-контейнеры healthy.

## Следующий шаг

Отправить новое сообщение в личный чат аккаунта Виктории и проверить реальный Business update. Старые сообщения Telegram повторно не доставляет.

Связано: [[05_Решения/Telegram Business сообщения обрабатываются через общий HR webhook]]
