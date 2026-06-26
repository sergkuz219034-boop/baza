# TrafficHub offers and conversions

## Назначение
`offers` хранит нормализованные офферы партнёрских сетей. `conversions` хранит конверсии/postback-события и должна ссылаться на `offers.id`, если оффер известен локально.

## Подтверждённые таблицы
- `offers`: локальный каталог офферов по сети, tenant и владельцу.
- `conversions`: события конверсий, включая `raw_data` от внешней сети.
- `postback_logs`: сырые события postback/API-синхронизации.

## Owner-scoped модель
Связь офферов и конверсий должна учитывать:
- `network`;
- `tenant_id`;
- `owner_username`;
- внешний ID оффера (`offers.external_id` и `conversions.raw_data->>'offer_id'`).

Это нужно, чтобы один пользователь не видел/не подхватывал офферы другого пользователя.

## LeadSU
Для LeadSU часть конверсий приходит только с `offer_id`, без человекочитаемого `offer_name`. Поэтому синхронизация должна сначала подтянуть каталог офферов через LeadSU API, затем импортировать конверсии.

Подтверждённое поведение после исправления 2026-06-26:
- `_sync_leadsu_conversions` вызывает `get_offers()` перед импортом конверсий;
- офферы upsert-ятся в `offers`;
- `_import_network_conversions` получает `offer_index` и заполняет `conversions.offer_id`;
- если в конверсии не было `offer_name`, он дописывается в `raw_data.offer_name` из локального оффера;
- старые конверсии довязываются backfill-логикой.

## Почему это важно
Если локального оффера нет, UI вынужден показывать fallback `Оффер #<external_id>`. Это технически корректно, но для пользователя выглядит как несинхронизированные данные.

## Диагностика
Проверить несвязанные LeadSU-конверсии:

```sql
select raw_data->>'offer_id' as raw_offer_id, count(*)
from conversions
where network = 'leadsu' and offer_id is null
group by 1;
```

Проверить последние связи:

```sql
select c.id, c.owner_username, c.raw_data->>'offer_id', c.raw_data->>'offer_name', o.name
from conversions c
left join offers o on o.id = c.offer_id
where c.network = 'leadsu'
order by c.id desc
limit 20;
```
