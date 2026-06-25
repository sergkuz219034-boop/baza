# Lovko sync

## Что это

Синхронизация статистики Lovko из партнёрской сети в TrafficHub runtime database.

## Где находится

- `/root/TrafficHub/traffic_hub/api/routers/integrations.py`
- функция `_sync_network(..., OfferNetwork.lovko, tenant_id, username)`
- функция `_import_lovko_offer_stats(...)`

## Ownership

Данные Lovko должны быть scoped по:

- `tenant_id`
- `owner_username`
- `network = lovko`
- `external_offer_id`

Если legacy-строка была создана без owner, при первом подтверждённом sync она переносится на текущего owner и текущий tenant.

## Подтверждённый баг 2026-06-25

`_sync_network()` передавал `tenant_id`, но `_import_lovko_offer_stats()` не принимала этот аргумент.

Симптом в логах:

```text
TrafficHub: lovko sync error for artem: _import_lovko_offer_stats() got an unexpected keyword argument 'tenant_id'
```

Исправление в commit `5d9fc210a`:

- функция принимает `tenant_id`;
- новые строки создаются с tenant;
- legacy rows при adoption получают новый `tenant_id`;
- добавлена regression-проверка в `tests/test_integrations_sync.py`.

## Как проверять

1. После рестарта контейнера дождаться partner sync.
2. В логах `autolead_server_bot` должна быть строка вида:

```text
TrafficHub: lovko sync ok parsed=... imported=... for artem
```

3. Не должно быть `unexpected keyword argument 'tenant_id'`.

## Связанные заметки

- [[TrafficHub app]]
- [[Runtime database]]
- [[Ownership model]]
