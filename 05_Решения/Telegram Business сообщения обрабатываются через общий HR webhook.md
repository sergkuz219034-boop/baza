# Telegram Business сообщения обрабатываются через общий HR webhook

## Проблема

Обычный `message` и сообщение из автоматизации бизнес-аккаунта имеют разные update-типы и правила исходящей доставки.

## Контекст

Telegram Business присылает `business_message` с `business_connection_id`. Ответ без этого идентификатора не отправляется от имени подключённого бизнес-аккаунта.

## Решение

- Использовать канонический HR webhook для обычных и Business-сообщений.
- Явно подписывать webhook на `business_connection`, `business_message`, `edited_business_message`, `deleted_business_messages`.
- Читать `business_connection_id` из вложенного `business_message.business_connection_id`, затем сохранять его в owner-scoped состоянии кандидата.
- Передавать идентификатор в `sendMessage` и follow-up доставку.
- События `business_connection` сохранять в owner-scoped `HrAgentChannelBinding.extra_config.business_connections`; enabled/disabled состояние является каноническим признаком фактического подключения аккаунта, а не зелёный `getWebhookInfo` сам по себе.
- Пока LLM формирует ответ, отправлять `sendChatAction(action=typing)` с тем же `business_connection_id`: сразу при получении сообщения и затем каждые четыре секунды.
- Перед `sendMessage` выдерживать ограниченную паузу `0,8–4,0` секунды с поправкой на длину ответа и jitter. Ошибка chat action не должна прерывать основной ответ.

## Последствия

- Один bot token обслуживает прямой диалог с ботом и автоматизацию аккаунта.
- Пользовательская Telethon-сессия Виктории не нужна для Business-ответов.
- Подключение выполняется владельцем в Telegram Business для каждого аккаунта; сервер не может создать Business connection только по сохранённой Telethon session.
- Потеря или дублирование user session не должно отключать основной webhook-контур.
- Если `business_connection_id` потерян, Telegram примет обычный `sendMessage`, но ответ появится в личке с ботом, а не в чате бизнес-аккаунта.
- Статус `typing` живёт не более пяти секунд, поэтому интервал обновления выбран короче этого окна; пауза ограничена, чтобы не увеличивать время webhook без верхней границы.

## Альтернативы

- Telethon user session: отклонена как основной путь из-за `AuthKeyDuplicatedError` и зависимости от уникального IP/session usage.
- Отдельный Business worker: пока не нужен, так как общий HR state machine уже реализует обработку и доставку.

Связано: [[01_Расследования/2026-07-09 Город и Telegram Business Виктории]], [[01_Расследования/2026-07-15 Telegram HR Agent и Business аккаунты]]
