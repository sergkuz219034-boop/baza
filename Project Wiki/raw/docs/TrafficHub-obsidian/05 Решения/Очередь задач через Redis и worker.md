# Очередь задач через Redis и worker

## Проблема

Старая модель “один процесс выполняет всё сам” не объясняет текущее поведение jobs, busy-state и realtime status.

## Контекст

- live compose `2026-06-11` содержит отдельные контейнеры `traffichub_worker` и `traffichub_redis`;
- live `traffic_hub/services/job_queue.py` подтверждает Redis contract:
  - queue `traffic_hub:jobs:queue`
  - state `traffic_hub:jobs:state:<owner>`
  - active set `traffic_hub:jobs:active`
  - events channel `traffic_hub:jobs:events`
- live `traffic_hub/worker.py` подтверждает, что worker берёт job через `job_queue.claim_next_job()` и слушает event bridge;
- live `api/server.py` и `api/ws_manager.py` подтверждают websocket bridge для status/log.

## Решение

Считать канонической моделью:

- enqueue в web/API контейнере;
- исполнение в отдельном worker;
- Redis как state/queue/event layer;
- websocket bridge в `api/server.py` и `api/ws_manager.py`;
- каждый owner job исполняется отдельным subprocess внутри `traffichub_worker`;
- thread-параллельность внутри одного worker process не использовать.
- лимит параллельных owner jobs задаётся через `WORKER_MAX_PARALLEL_OWNERS`;
- на текущем live server дефолт установлен в `2`.

## Последствия

- для багов запуска нужно смотреть не только API, но и worker + Redis;
- UI может быть в рассинхроне с backend-state, поэтому `/api/jobs/status` и Redis важнее визуального pill;
- старые документы про in-memory scheduler без worker нужно переписывать;
- real multi-owner parallel теперь разрешён и подтверждён runtime на debug-owner'ах;
- owner log isolation удерживается не глобальной сериализацией, а process boundary;
- stop-path для живого subprocess идёт через:
  - `request_stop(owner)`
  - Redis event `job_stop_requested`
  - `SIGTERM` в owner subprocess;
- история job-state должна сохранять `started_at` и `finished_at` после завершения;
- shutdown-path worker сначала переводит активные jobs в `stopping`, чтобы service restart не выглядел как business error;
- если понадобится ограничить нагрузку, делать это через лимит subprocess capacity, а не через возврат к global single-flight.

## Альтернативы

- One-process in-memory execution.
  - Противоречит текущему runtime и коду.
- Thread-параллельность внутри одного worker process.
  - Ломает ownership у `redirect_stdout()` и `vbiv_bot._active_ctx`.
