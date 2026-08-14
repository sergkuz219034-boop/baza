# 2026-06-30 alex run_log stuck running after stop

## Симптом

- В `autolead_run_log` у `alex` остались две строки `status='running'` без `finished_at`, хотя пользовательский job уже был остановлен.

## Зона системы

- `traffic_hub/worker.py`
- `traffic_hub/services/job_queue.py`
- `utils/runtime_store_pg_logs.py`
- PostgreSQL table `autolead_run_log`
- Redis keys `traffic_hub:jobs:state:<owner>` и `traffic_hub:jobs:progress:<owner>`

## Гипотеза

- При `SIGKILL`/force-kill subprocess код внутри `services/leads_service.py::run_full_cycle()` не успевает вызвать `finish_run()`.
- Worker переводит Redis job-state в `idle`, но не закрывает открытые PostgreSQL run-log строки owner.

## Проверка

- Live Redis `traffic_hub:jobs:state:alex` показывал `status=idle`, `finished_at=2026-06-30 07:22:05`.
- В `docker exec traffichub_worker ps aux` не было активного `traffic_hub.job_process` для `alex`.
- В PostgreSQL до исправления:
  - `alex`, `started_at=2026-06-30 07:03:31`, `status=running`, `finished_at=NULL`;
  - `alex`, `started_at=2026-06-30 07:10:07`, `status=running`, `finished_at=NULL`.
- Логи worker показывали `Worker force-killed owner=alex ... after 2.5s stop grace`.

## Наблюдение

- Root cause подтверждён кодом: `traffic_hub/worker.py` при `_finalize_process_exit()` и `_escalate_stopping_processes()` вызывал `job_queue.transition_job(...)`, но не закрывал `autolead_run_log`.
- Исправление:
  - `utils/runtime_store_pg_logs.py::finish_running_runs_for_owner()` закрывает только `running` строки конкретного owner.
  - `utils/database.py::finish_running_runs_for_owner()` экспортирует функцию в runtime facade.
  - `traffic_hub/worker.py` закрывает dangling run-log при `job_stop`, `job_done` и `job_error`.
  - `tests/test_worker_parallel.py` покрывает stop и failed subprocess.
- Тесты:
  - targeted: `12 passed`;
  - full: `398 passed, 43 skipped`.
- Product commit: `6c26c5eb0 fix: close run logs when worker stops jobs`.
- GitHub checks: `CI=success`, `Build and Push Docker Image=success`.
- Live deploy: `autolead_bot` и `worker` пересозданы, оба `healthy`, `/api/health` возвращает `ok`.
- Live cleanup: две старые строки `alex` закрыты как `stopped`.
- Финальная проверка PostgreSQL: `select ... where status='running' or finished_at is null` вернул `0 rows`.

## Вывод

- Баг был общесистемным для всех пользователей: любой force-kill job мог оставить `autolead_run_log` в `running`.
- Исправление находится в общем worker lifecycle, поэтому распространяется на всех текущих и будущих пользователей.
- Redis/job-state и PostgreSQL run-log теперь синхронизируются при остановке или падении subprocess.

## Следующий шаг

- При следующем live full-cycle проверить, что после обычной остановки строка run-log закрывается сразу, без ожидания restart reconciliation.
