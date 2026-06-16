# Job Queue

## Назначение

User-scoped очередь задач для команд:

- `upload`
- `run`
- `send`
- `scrape`
- `automode`
- `superjob`

## Подтверждённые точки кода

- Live code:
  - `traffic_hub/services/job_queue.py`
  - `traffic_hub/services/job_runner.py`
  - `traffic_hub/worker.py`
  - `api/ws_manager.py`
  - `api/server.py`
- Локальный bundle содержит старые partial copies этих же зон, но каноном считать live server code.

## Storage / transport

- Queue: Redis list `traffic_hub:jobs:queue`
- State per owner: `traffic_hub:jobs:state:<owner>`
- Active owners set: `traffic_hub:jobs:active`
- Event bus: Redis pubsub channel `traffic_hub:jobs:events`
- Progress: `traffic_hub:jobs:progress:<owner>`
- Stop flag: `traffic_hub:jobs:stop:<owner>`

## Статусы

- `queued`
- `running`
- `stopping`
- `idle`
- `error`

## Runtime contract

- Busy statuses:
  - `queued`
  - `running`
  - `stopping`
- Terminal statuses:
  - `idle`
  - `error`
- Last command:
  - `last_command` хранит последнюю команду owner для финальных status/log events, когда `command` уже очищен при переходе в `idle`
- Timestamps:
  - `started_at` должен переживать переход `running -> idle`
  - `finished_at` должен выставляться в terminal state
- Stale busy state:
  - автоматически лечится после `6` часов через `STALE_BUSY_AFTER`
  - healed state переводится в `error`
- Stop path:
  - `request_stop_for_job()` вызывает `utils.state.request_stop(owner)`
  - затем публикует event `job_stop_requested`
  - `traffichub_worker` ловит `job_stop_requested`, отправляет owner subprocess `SIGTERM` и, если процесс не вышел быстро, эскалирует в `SIGKILL`
- Fallback:
  - при недоступном Redis очередь и state могут упасть в in-memory backend

## Поведение

- очередь owner-scoped по state, но физически общая по Redis list;
- busy-check идёт по state owner;
- повторный запуск при busy не падает 409 наружу, а возвращает `202 already_running`;
- финальный state публикуется в websocket bridge и читается frontend.
- stop-path должен менять UI немедленно:
  - `api/routers/jobs.py::stop_job()` возвращает owner status сразу после `request_stop_for_job(owner)`;
  - frontend обязан делать `refreshJobStatus()` сразу после POST `/api/jobs/stop`, а не ждать следующего poll/websocket.
- с 2026-06-11 worker исполняет только один job одновременно, чтобы не ломать owner-scoped логирование через `redirect_stdout()`.
- с 2026-06-12 status events очереди дополнительно конвертируются в owner-scoped live-log строки:
  - `в очереди`
  - `в работе`
  - `выполняется`
  - `остановка`
  - `остановлена`
  - `завершена`
  - `ошибка`
- для длинных `running/stopping` задач API шлёт heartbeat в live-log примерно раз в `15` секунд.
- текущий пользовательский формат heartbeat намеренно короткий:
  - `Выгрузка: выполняется`
  - `Рассылка: выполняется`
  - `Полный цикл: выполняется`
- детальные progress counters не должны быть частью основной пользовательской ленты.
- realtime spinner в логах — это frontend-derived state, а не отдельный server log record:
  - строка должна жить, пока owner job находится в `queued/running/stopping`;
  - обычные log lines не должны удалять spinner-строку;
  - timestamp spinner-строки должен показываться слева так же, как у обычных log lines.
- worker забирает задачи через `claim_next_job()`:
  - blocking path через `BLPOP`, когда active processes нет;
  - non-blocking path через `LPOP`, когда worker добирает ещё owner jobs в свободную capacity;
- дополнительный цикл блокировки есть в `leads_service.try_acquire_cycle_lock(owner)`, даже после успешного enqueue.
- На `2026-06-14` live runtime обновлён:
  - внутри одного `traffichub_worker` job больше не исполняются через thread;
  - каждый owner job стартует отдельным subprocess `python -m traffic_hub.job_process`;
  - следствие:
    - owner `A` и owner `B` могут одновременно быть `running`;
    - owner-изоляция логов сохраняется через отдельный process-local logging setup.
  - на текущем production server дефолтный лимит:
    - `WORKER_MAX_PARALLEL_OWNERS=2`
  - причина:
    - `2 vCPU`
    - высокий load average
    - заполненный swap

## Известные риски

- если UI показывает старый статус при `Redis=idle`, искать баг в websocket/poll слое;
- stale busy state лечится внутри `job_queue.py`, но это только safety net;
- для реального анализа всегда нужен owner-specific state, а не общий вывод “ничего не работает”.
- `app_log` нельзя было считать изолированным при возврате к параллельному исполнению через thread внутри одного worker process.
- `modules/vbiv_bot.py` по-прежнему хранит global `_active_ctx`, поэтому parallel Playwright jobs внутри одного процесса всё ещё unsafe.
- Актуальная защита от этого риска:
  - параллельность делается не thread-ами, а subprocess-per-owner.
- `send` и `retry_queue` нельзя смешивать в отладке:
  - кнопка `Рассылка` работает по `leads`;
  - `retry_queue` обрабатывается только внутри `Полного цикла`.
- Worker restart во время активного job всё ещё maintenance-sensitive:
  - owner может получить `error=Worker restarted before job finished`
  - это side effect service restart, а не бизнес-ошибка оффера.
  - с `2026-06-14` shutdown-path worker сначала переводит активные jobs в `stopping`, чтобы снизить число таких ложных ошибок.
- Owner stop теперь двухступенчатый:
  - worker ведёт `_STOP_REQUESTED_AT` per owner;
  - дефолтный grace period задаётся `WORKER_STOP_GRACE_SECONDS`, live default `2.5s`;
  - это защита от зависания на длинных `page.goto()`/network waits внутри Playwright subprocess.

## См. также

- [[01 Расследования/2026-06-15 Вкладка вакансий показывает реальное количество кандидатов для приглашения]]
- [[01 Расследования/2026-06-15 Realtime spinner в логах больше не удаляется обычными строками]]
