# 2026-06-14 Stop request lag и stop-сигнал без ⛔

## Симптом

- Пользователь нажимал `Остановить`, но задача не реагировала мгновенно.
- В логе stop-request не был явно помечен красным `⛔`.

## Зона системы

- Live code:
  - `/root/TrafficHub/modules/vbiv_bot.py`
  - `/root/TrafficHub/api/server.py`
  - `/root/TrafficHub/dashboard/app.js`

## Гипотеза

- Stop-request доходил до state/queue, но часть sender-runtime ждала старый `stop_event.wait(timeout=delay)`, который не будился owner-specific stop-флагом.
- Frontend/UI-path удалял `⛔` из текста и не классифицировал такие строки как error-level.
- В live API process оставался старый mapping `job_stop_requested -> [i] ...`, пока контейнер не был явно перезапущен.
- Даже после фикса delay-path задача могла висеть на длинном `page.goto()`/Playwright timeout:
  - API process вызывал `interrupt_current_context()` не в том процессе, где реально живёт браузер;
  - worker останавливал owner subprocess только мягким `SIGTERM`, без эскалации.

## Проверка

- По live коду подтверждено:
  - `job_queue.request_stop_for_job()` сразу переводит owner state в `stopping`;
  - `modules/vbiv_bot.py` имел два legacy места с `stop_event.wait(timeout=delay)`;
  - owner-specific `request_stop(owner)` не обязан мгновенно будить эти ожидания.
- На `2026-06-14` внесён fix:
  - `modules/vbiv_bot.py`
    - добавлен owner-aware `_wait_with_stop()`;
    - оба `stop_event.wait(timeout=delay)` заменены на interruptible polling с шагом `0.25s`;
  - `api/server.py`
    - `job_stop_requested` теперь:
      - `level = "ERROR"`
      - `msg = "[⛔] <команда>: остановка"`
  - `dashboard/app.js`
    - `[⛔]` теперь классифицируется как `ERROR`;
    - `cleanLogMessageText()` больше не удаляет `⛔`, а сохраняет его в user-facing строке.
- Дополнительная live-проверка по server code подтвердила:
  - активный Playwright context живёт внутри `traffic_hub.job_process`, а не в API process;
  - `api/routers/jobs.py` вызывает `modules.vbiv_bot.interrupt_current_context()`, но этот вызов не может прервать браузер другого subprocess;
  - `traffic_hub/worker.py` ранее вызывал только `process.terminate()`, поэтому зависший subprocess мог доживать до network/browser timeout.
- На live server добавлен второй слой stop-fix:
  - `traffic_hub/worker.py`
    - введён owner-scoped stop grace timer `_STOP_REQUESTED_AT`;
    - `_terminate_process(owner)` теперь работает как `terminate -> kill`;
    - если subprocess не вышел за `WORKER_STOP_GRACE_SECONDS` (дефолт `2.5s`), worker делает `process.kill()`;
    - основной loop worker теперь вызывает `_escalate_stopping_processes()` на каждом цикле.
- Runtime proof на debug owner `debug-worker-d` после явного restart `autolead_bot`:
  - enqueue:
    - `status=queued`
  - stop request через `0.5s`:
    - `status=stopping`
  - через `~1s`:
    - `status=idle`
  - `app_log`:
    - `2026-06-14 20:01:13 [i] Полный цикл: в очереди`
    - `2026-06-14 20:01:13 [⛔] Полный цикл: остановка`
    - `2026-06-14 20:01:13 [⛔] Полный цикл: остановлен`

## Наблюдение

- До явного `docker compose restart autolead_bot` контейнерный process держал старую версию `api/server.py`, поэтому промежуточный stop-request ещё писал `[i] ...`.
- После restart live mapping стал корректным.
- Stop-path на уровне process boundary был split-brain:
  - UI/API честно ставил owner в `stopping`;
  - job subprocess видел stop-флаг только кооперативно;
  - зависший Playwright участок не обязан был быстро вернуться в Python, поэтому один `SIGTERM` не гарантировал мгновенную остановку.

## Вывод

- Stop-path теперь:
  - быстрее реагирует на owner-specific `/stop` во внутренних delay-wait участках sender-runtime;
  - отображает stop-request как явный красный `⛔` сигнал в логе;
  - оставляет `⛔` и на финальной строке `остановлен`.
- Дополнительный канон после live-fix:
  - мгновенная остановка длинного browser wait обеспечивается не API-side `interrupt_current_context()`, а worker-side эскалацией `SIGTERM -> SIGKILL` для owner subprocess.

## Следующий шаг

- Когда лимит серверных проверок снова позволит живой smoke:
  - повторить debug-run со stop во время реального открытия оффера;
  - подтвердить, что `status=stopping -> idle` укладывается в `~3s`, а в `app_log` остаются строки `⛔ остановка` и `⛔ остановлен`.
