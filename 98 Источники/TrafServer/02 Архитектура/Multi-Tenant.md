# Multi-Tenant

Теги: #архитектура #tenant-isolation

## Каноническое правило

Tenant isolation строится вокруг `owner_username`.

## Где это видно

- runtime БД: `autolead.db`
- TrafficHub business schema
- `traffic_hub/api/ownership.py`
- `remote_files/tests/test_traffic_tenant_isolation.py`

## Подтверждённое поведение

- operator видит только свои offers, leads, messengers, funnels, finance, stats;
- admin видит глобальный набор;
- новые записи создаются с owner текущего пользователя;
- websocket broadcast идёт на конкретного пользователя, а не глобально.

## Почему это важно

Tenant isolation добавлялся миграциями `0005`-`0007`, поэтому старые данные и legacy-таблицы особенно чувствительны к drift.

## Смежные страницы

- [[Database]]
- [[Authorization]]
