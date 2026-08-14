# Проверка Redis job state TTL

## Когда использовать

Если UI показывает старый статус запуска, странный progress, зависшую остановку или старые debug/test owners.

## Шаги

1. Проверить активные runtime keys:

```bash
docker exec traffichub_redis redis-cli --scan --pattern "traffic_hub:jobs:*"
```

2. Проверить TTL user-scoped ключей:

```bash
docker exec traffichub_redis redis-cli ttl traffic_hub:jobs:progress:artem
docker exec traffichub_redis redis-cli ttl traffic_hub:jobs:state:artem
```

3. Если TTL `-1`, значит код или ручная операция снова создали бессрочный Redis state.

4. Если ключ относится к debug/test owner и нет активной задачи, его можно удалить:

```bash
docker exec traffichub_redis redis-cli del traffic_hub:jobs:progress:debug-worker-a
```

5. Реальные пользовательские ключи не удалять без проверки `traffic_hub:jobs:active` и текущего статуса job.

## Норма после `e4818e56a`

- `traffic_hub:jobs:progress:*` имеет TTL 7 дней.
- `traffic_hub:jobs:state:*` имеет TTL 7 дней.
- `traffic_hub:jobs:stop:*` имеет TTL 6 часов.

