# 2026-06-14 Worker serializes all owners while one job is active

## Симптом

- Owner `artem2` получил статус:
  - `[i] Рассылка: в очереди`
- Redis queue содержала job:
  - `LLEN traffic_hub:jobs:queue = 1`
- Но job не стартовал сразу, хотя `traffichub_worker` был healthy.

## Зона системы

- Live code:
  - `/root/TrafficHub/traffic_hub/worker.py`
  - `/root/TrafficHub/traffic_hub/services/job_queue.py`
  - `/root/TrafficHub/traffic_hub/services/job_runner.py`
  - `/root/TrafficHub/modules/vbiv_bot.py`
- Live runtime:
  - Redis keys:
    - `traffic_hub:jobs:queue`
    - `traffic_hub:jobs:state:<owner>`
    - `traffic_hub:jobs:active`

## Гипотеза

- Это не dead worker и не потерянная задача.
- Worker deliberately serializes jobs globally, пока любой owner уже активен.

## Проверка

- По Redis в момент расследования подтверждено:
  - active owners:
    - `alex`
    - `artem2`
  - queue length:
    - `1`
- По live log `traffichub_worker` подтверждено:
  - worker реально выполнял длинный `run` для `alex`
  - в это же время `artem2` оставался queued
- По live-коду `traffic_hub/worker.py` подтверждено:
  - main loop делает:
    - `_prune_finished_threads()`
    - `if _active_owners_snapshot(): continue`
    - `job_queue.claim_next_job(timeout=1)` только когда активных owner нет вообще
- По live-коду `modules/vbiv_bot.py` подтверждено:
  - активный Playwright context хранится глобально:
    - `_active_ctx`
    - `_active_ctx_thread_id`
- По live-коду `traffic_hub/services/job_runner.py` подтверждено:
  - job execution использует `redirect_stdout()` в owner-scoped logger bridge

## Наблюдение

- Текущая модель действительно owner-scoped по state и app-log.
- Но исполнение job внутри одного `traffichub_worker` сейчас фактически глобально последовательное.
- Причина не только в желании упростить queue, а в runtime-ограничениях:
  - `redirect_stdout()` делает параллельные job-thread рискованными для owner-scoped print/log;
  - глобальный `_active_ctx` в `vbiv_bot.py` делает параллельный Playwright в одном процессе небезопасным.

## Вывод

- На момент расследования это действительно было нормальным runtime-поведением, а не потерянной задачей.
- Корень проблемы был архитектурный:
  - `traffic_hub/worker.py` блокировал `claim_next_job()` пока жив любой active owner;
  - `traffic_hub/services/job_runner.py` использовал `redirect_stdout()` внутри одного процесса;
  - `modules/vbiv_bot.py` держал global `_active_ctx`.

## Следующий шаг

- Историческое ограничение зафиксировано и больше не является каноном.
- На `2026-06-14` оно снято через owner-isolated subprocess execution:
  - worker больше не исполняет jobs в thread внутри одного процесса;
  - каждый owner job стартует отдельным `python -m traffic_hub.job_process`;
  - stop/progress/state продолжают идти через Redis;
  - owner-scoped app logs подтверждены на runtime для `debug-worker-a` и `debug-worker-b`.
- Актуальное follow-up расследование:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Worker переведён на subprocess-per-owner и разрешил multi-owner parallel]]
