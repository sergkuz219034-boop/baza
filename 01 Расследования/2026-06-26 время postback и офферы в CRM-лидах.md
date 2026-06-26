# 2026-06-26 время postback и офферы в CRM-лидах

## Симптом
В `TrafficHub -> Лиды` время создания отличалось от времени в кабинете партнёрки, а колонка `Оффер` была пустой.

## Зона системы
`traffic_hub/api/routers/postbacks.py`, `traffic_hub/api/routers/leads.py`, таблицы `conversions`, `postback_logs`, UI `dashboard/app.js`.

## Гипотеза
CRM-лиды используют `Conversion.received_at` вместо времени действия из partner payload. Название оффера не видно, потому что Leads.su присылает только `offer_id`, а локальная таблица `offers` не содержит соответствующих записей.

## Проверка
На сервере в PostgreSQL последние Leads.su postback payload содержат:
- `created`: `2026-06-26 12:07:36`, `2026-06-26 11:52:39`;
- `offer_id`: `982`, `10083`;
- `offer_name` отсутствует.

В `offers` и `network_offer_stats` записей для `982/10083` не найдено.

## Наблюдение
До фикса `/traffic-api/leads` отдавал `created_at = conv.received_at`, поэтому UI показывал время обработки сервером. Оффер строился только из `Offer.name` или `raw.offer_name/raw.offer`.

## Вывод
Для CRM-лидов нужно отображать время события из postback `raw.created`, а если название оффера не пришло и локальный оффер не найден, показывать fallback `Оффер #<offer_id>`.

## Что изменено
- В `traffic_hub/api/routers/leads.py` добавлен helper для чтения фактического времени события из raw payload.
- В CRM-лидах `created_at` теперь берётся из `raw.created` при наличии.
- В CRM-лидах `offer_name` теперь восстанавливается из raw offer-name ключей или fallback `Оффер #offer_id`.
- Live container `traffichub_app` пересобран и проверен как healthy.

## Проверка после фикса
Сериализация последних конверсий из live БД:
- `42 -> Оффер #982 -> 2026-06-26 12:07:36`;
- `41 -> Оффер #10083 -> 2026-06-26 11:52:39`.

## Следующий шаг
Для настоящих названий вроде `T-Банк HR [sale]` нужно синхронизировать справочник офферов Leads.su API в `offers` или `network_offer_stats`, потому что сам postback это название сейчас не присылает.
