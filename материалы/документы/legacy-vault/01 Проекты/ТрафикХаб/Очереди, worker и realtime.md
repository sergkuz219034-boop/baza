# Очереди, worker и realtime

## Что подтверждено

- queue backend: Redis
- worker model: subprocess-per-owner
- публичный status/log bridge идёт через web/API слой

## Ключи и каналы

- queue: `traffic_hub:jobs:queue`
- state: `traffic_hub:jobs:state:<owner>`
- progress: `traffic_hub:jobs:progress:<owner>`
- stop: `traffic_hub:jobs:stop:<owner>`
- events: `traffic_hub:jobs:events`

## Статусы

- `queued`
- `running`
- `stopping`
- `idle`
- `error`

## Практические инварианты

- owner `A` и owner `B` могут работать параллельно;
- внутри одного owner второй запуск не должен создавать вторую job, а возвращает `already_running`;
- stop должен менять UI сразу, а не после длинной задержки;
- realtime лог должен показывать живую работу без шумного спама и без потери финального статуса.

## Что важно для дебага

- если UI “висит”, сначала сравни:
  - `/api/jobs/status`
  - Redis state owner
  - worker log
  - web websocket bridge
- если лог пустой, это не означает, что worker idle: нужно проверить owner-state и контейнер `traffichub_worker`;
- если проблема выглядит как “ничего не запускается у всех”, сначала проверять Redis/worker, а не офферы.
