# 2026-06-14 Worker переведён на subprocess-per-owner и разрешил multi-owner parallel

## Симптом

- До фикса один длинный `run` любого owner блокировал старт job других owner.
- Пользователь попросил больше не проверять это на боевых профилях и использовать отдельный debug-профиль.

## Зона системы

- Live code:
  - `/root/TrafficHub/traffic_hub/worker.py`
  - `/root/TrafficHub/traffic_hub/job_process.py`
  - `/root/TrafficHub/traffic_hub/log_setup.py`
  - `/root/TrafficHub/traffic_hub/services/job_queue.py`
  - `/root/TrafficHub/traffic_hub/services/job_runner.py`
  - `/root/TrafficHub/modules/vbiv_bot.py`
- Live runtime:
  - `traffichub_worker`
  - `autolead_server_bot`
  - Redis keys `traffic_hub:jobs:*`

## Гипотеза

- Реальную multi-owner параллельность нельзя безопасно вернуть через thread внутри одного worker process.
- Безопасный путь:
  - оставить Redis queue/state/event contract как есть;
  - вынести исполнение каждого owner job в отдельный subprocess.

## Проверка

- По live-коду до фикса подтверждено:
  - `traffic_hub/worker.py` не делал `claim_next_job()`, пока `_active_owners_snapshot()` не пуст;
  - `job_runner.py` использовал `redirect_stdout()` для owner log bridge;
  - `vbiv_bot.py` хранил process-global `_active_ctx`.
- На сервере внесены изменения:
  - добавлен `traffic_hub/job_process.py` для исполнения одной owner job в отдельном процессе;
  - logging setup вынесен в `traffic_hub/log_setup.py`;
  - `traffic_hub/worker.py` переведён с thread registry на process registry;
  - `traffic_hub/services/job_queue.py` получил non-blocking `claim_next_job(timeout=0)` path через `LPOP`.
- Regression coverage:
  - `tests/test_worker_parallel.py`
  - `tests/test_jobs_router.py`
  - `tests/test_proxy_config.py`
  - `tests/test_retry_queue_matching.py`
  - `tests/test_leadsu_blank_recovery.py`
- Helper-container pytest на live tree:
  - `14 passed`
- Runtime-safe проверка проведена не на боевых owner, а на:
  - `debug-worker-a`
  - `debug-worker-b`
- Дополнительная controlled проверка проведена на:
  - `debug-worker-a`
  - `debug-worker-b`
  - `debug-worker-c`
  - `debug-worker-d`
- Результат runtime-проверки:
  - обе задачи `run` были одновременно в `status=running`;
  - одинаковый `started_at`:
    - `2026-06-14 16:32:56`
  - обе завершились в `idle`;
  - owner-scoped app logs сохранились отдельно для каждого debug-owner.
- После ввода лимита `WORKER_MAX_PARALLEL_OWNERS=2` подтверждено:
  - `debug-worker-a` и `debug-worker-b` стартуют первыми;
  - `debug-worker-c` и `debug-worker-d` остаются `queued`;
  - после освобождения capacity вторая пара доходит до `idle`;
  - финальный state сохраняет `started_at` и `finished_at`.

## Наблюдение

- Перевод на subprocess сохранил:
  - Redis owner state;
  - stop flags;
  - progress counters;
  - owner-scoped app logs.
- Исторический глобальный single-flight барьер снят.
- Ограничение теперь не архитектурное, а ресурсное.
- На live server подтверждено:
  - `2 vCPU`
  - `~3.9 GB RAM`
  - swap полностью занят
  - load average около `12`
- Поэтому `WORKER_MAX_PARALLEL_OWNERS=0` для этого сервера unsafe.
- В runtime установлен дефолт:
  - `WORKER_MAX_PARALLEL_OWNERS=2`
- Дополнительно найден и исправлен дефект истории статусов:
  - `traffic_hub/services/job_queue.py::transition_job()` раньше затирал `started_at=None` из исходного job payload;
  - после фикса финальный `idle` state сохраняет реальный `started_at`.
- Дополнительно смягчён shutdown-path worker:
  - перед остановкой активные jobs переводятся в `stopping`;
  - это уменьшает ложные `error=Worker restarted before job finished` после service restart.

## Вывод

- На `2026-06-14` live runtime больше не канонически последовательный.
- Актуальная модель:
  - queue/state/event layer остаются Redis-based;
  - один owner = один subprocess;
  - multi-owner parallel разрешён;
  - owner-isolation логов подтверждена.
- Для текущей production-машины safe default:
  - не больше `2` owner jobs одновременно.

## Следующий шаг

- Все дальнейшие smoke-проверки parallel behavior делать только через debug-owner'ы, а не через `admin/alex/artem`.
- Для production-нагрузки отдельно наблюдать:
  - число одновременно открытых Playwright browser/process;
  - memory pressure;
  - docker/container restart patterns.
- Если появятся симптомы resource exhaustion, следующим слоем вводить не глобальную сериализацию, а явный лимит `WORKER_MAX_PARALLEL_OWNERS`.
