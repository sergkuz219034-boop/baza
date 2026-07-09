# Подключение Telegram HR бота

## Симптом

Форма требовала `Webhook secret` и вакансию по умолчанию. Без ручного секрета API отвечал `Webhook secret is required`. Даже сохранённая привязка не регистрировала webhook в Telegram.

## Зона системы

- `AccountManager/dashboard/index.html`
- `AccountManager/dashboard/app.js`
- `AccountManager/api/routers/hr_agent.py`
- `traffic_hub/api/routers/hr_agent.py`
- таблица `hr_agent_channel_bindings`

## Гипотеза

Для подключения Telegram HR-бота пользователю достаточно названия и bot token. Секрет webhook должен быть внутренним и генерироваться сервером.

## Проверка

- Прослежены create/update binding и публичный webhook endpoint.
- Проверено отсутствие вызова Telegram `setWebhook`.
- Проверен штатный заголовок Telegram `X-Telegram-Bot-Api-Secret-Token`.
- Прогнаны `tests/test_hr_agent_router.py`.
- Выполнена регистрация live-бота и проверен `getWebhookInfo`.

## Наблюдение

- AccountManager требовал секрет вручную.
- Публичный endpoint принимал только внутренний `X-HR-Secret`, несовместимый с автоматическим `secret_token` Telegram.
- Выбор вакансии для создания binding технически не обязателен: сервис умеет выбрать первую активную вакансию.
- Первоначальный webhook был зарегистрирован на `traffic-hubcrm.ru`. Старый домен возвращал HTML-страницу «TrafficHub переехал» с HTTP 200, поэтому Telegram считал событие доставленным, но HR API его не получал.
- Неизменный query-параметр `/static/app.js?v=20260702-api-tabs-removed` оставлял в браузере старую версию интерфейса и вечный текст «Загрузка webhook-данных…».
- Повторное сохранение формы создало две привязки с одним bot token и разными секретами.

## Вывод

Подтверждено кодом и live:

- форма принимает только название и токен;
- сервер генерирует секрет через `secrets.token_urlsafe`;
- create/update вызывает Telegram `setWebhook`;
- endpoint принимает штатный Telegram secret header и сохраняет совместимость с `X-HR-Secret`;
- `default_vacancy_id` при подключении бота не задаётся;
- webhook строится из live `PUBLIC_BASE_URL`, сейчас `https://traffic-hub.pro`;
- повторное создание с тем же owner-scoped token обновляет существующий binding;
- версия статического JS изменяется при релизе формы;
- бот `@Vectoria101_bot` зарегистрирован на рабочем домене, Telegram сообщает `pending_update_count=0` и отсутствие последней ошибки;
- внешний synthetic webhook прошёл через Caddy до HR API и вернул `200 {"ok":true,"ignored":true,"reason":"empty_text"}`.

Изменения: product commits `f411ecd92`, `11aa94e66`. CI и Docker build зелёные.

## Следующий шаг

Отправить новое тестовое сообщение боту и проверить создание owner-scoped кандидата и исходящий ответ в live UI. Старые сообщения не будут повторены: старый домен уже ответил Telegram кодом 200.

Связано: [[05_Решения/Telegram HR бот подключается по названию и токену]]
