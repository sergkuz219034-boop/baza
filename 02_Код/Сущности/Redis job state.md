# Redis job state

## Назначение

Redis хранит краткоживущий runtime state очереди Autolead jobs:

- `traffic_hub:jobs:progress:<owner>` — progress counters из `utils/state.py`;
- `traffic_hub:jobs:state:<owner>` — статус job из `traffic_hub/services/job_queue.py`;
- `traffic_hub:jobs:stop:<owner>` — stop flag;
- `traffic_hub:jobs:queue` — очередь задач;
- `traffic_hub:jobs:active` — active owners.

## Подтверждённое поведение

После fix `e4818e56a` progress/state/stop keys не должны жить бесконечно:

- progress TTL: 7 дней;
- job state TTL: 7 дней;
- stop flag TTL: 6 часов.

## Почему так

Redis в этом контуре — runtime cache. Источник истины по пользователям, лидам, логам и настройкам находится в PostgreSQL/control store. Вечные Redis keys создают риск stale UI/status после рестартов, тестовых запусков и debug-сессий.

## Проверка

На сервере:

```bash
docker exec traffichub_redis redis-cli ttl traffic_hub:jobs:progress:artem
docker exec traffichub_redis redis-cli ttl traffic_hub:jobs:state:artem
```

Ожидаемо: положительное число секунд, не `-1`.

## Связанные заметки

- [[2026-06-23 TrafficHub full senior audit]]
- [[2026-06-24 Redis job state TTL hygiene]]
- [[Autolead runtime]]

