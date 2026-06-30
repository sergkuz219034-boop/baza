# БАГ-008: строка `Полный цикл выполняется` мигала в dashboard

## Симптом

В admin-dashboard строка текущей задачи (`Полный цикл выполняется`) исчезала и появлялась примерно раз в секунду во время активного job.

## Зона системы

- `dashboard/app.js`
- realtime-отрисовка log-terminal
- poll-based status sync через `syncRealtimeJobSpinner()`

## Гипотеза

Frontend на каждом poll удалял DOM-строку spinner-лога и создавал её заново, даже если текст статуса не менялся.

## Проверка

- В live runtime в контейнере `autolead_server_bot` проверен `/app/dashboard/app.js`.
- `syncRealtimeJobSpinner()` вызывал `removeRealtimeSpinnerLine()` до проверки изменения текста.
- После удаления тот же статус `Полный цикл: выполняется` добавлялся через `appendLog(..., spinner: true)`.

## Наблюдение

Причина была не в backend-job и не в логах БД, а в клиентской перерисовке:

- spinner-строка удалялась при каждом обновлении статуса;
- timestamp для spinner формировался заново через `currentMoscowTimestamp()`;
- визуально это выглядело как мигание строки.

## Вывод

Канон для realtime-строки job status:

- spinner удаляется только когда job выходит из состояний `queued` / `running`;
- если текст статуса не изменился, DOM-строка не пересоздаётся;
- перерисовка допустима только при реальном переходе состояния (`в очереди` -> `выполняется` -> завершение).

## Следующий шаг

- Проверить, что аналогичная схема не используется в других transient UI-виджетах dashboard.
- При следующем UI-рефакторинге вынести spinner-status в отдельный stateful renderer без прямого `querySelector('.log-spinner')`.

## Дополнение 2026-06-30

### Симптом

Пользователь сообщил, что `Полный цикл выполняется` всё ещё мигает после предыдущего фикса.

### Проверка

- Live `/root/TrafficHub/dashboard/app.js` и контейнерный `/app/dashboard/app.js` уже содержали in-place renderer `updateRealtimeSpinnerLine()`.
- `api/server.py::_push_status_loop` подтверждён как источник status heartbeat каждые 2 секунды.
- Остаточный эффект создавался не пересозданием строки, а перезаписью `.log-ts`: `jobCycleDurationTimestamp()` менял `HH:MM:SS`, хотя `status/command/job_id/msg` не менялись.

### Вывод

Канон уточнён: одинаковый heartbeat не должен менять DOM вообще. Duration/timestamp не входит в ключ перерендера spinner-строки.

### Фикс

- Product commit `50aa653da`: `dashboard/app.js::updateRealtimeSpinnerLine` сравнивает `line.dataset.renderKey`; ключ строится из `status`, `command`, `job_id` и `msg`, без timestamp.
- Regression test: `tests/test_dashboard_realtime_spinner.py` проверяет, что render key исключает duration timestamp и блокирует повторный rewrite той же DOM-строки.
- Live deploy: `traffichub_app` пересоздан, `/api/health` вернул `status=ok`, публичный `/app.js` содержит `line.dataset.renderKey`.

Связанное расследование: [[01_Расследования/2026-06-30 Dashboard full-cycle spinner heartbeat]].

## Дополнение 2026-06-30: Rabota loading spinner

После стабилизации `Полный цикл выполняется` в UI стал заметен другой transient source: `⠋ Загрузка откликов: 100...`.

Это не `syncRealtimeJobSpinner()`, а legacy console-spinner из `modules/rabota_api.py::_spin()`. В non-TTY worker/runtime он печатал обычные строки, а `utils/runtime_logging.py::is_ui_relevant_log()` явно пропускал `⠋ Загрузка ...` в dashboard.

Фикс product commit `cf12e5062`:

- Rabota spinner теперь печатается только в TTY;
- legacy `⠋/⠙/.../✓ Загрузка откликов|автоподбора` отбрасываются UI-фильтром;
- добавлен regression test в `tests/test_runtime_logging.py`;
- live пересозданы `traffichub_app` и `traffichub_worker`.

Связанное расследование: [[01_Расследования/2026-06-30 Rabota loading spinner in dashboard logs]].

## Дополнение 2026-06-30: stale active row после очистки логов

### Симптом

Dashboard показывал строку `Полный цикл выполняется` больше 3 минут, хотя серверная очередь уже была пустой.

### Проверка

- Live `job_queue.list_active_owners()` вернул пустой список.
- `docker logs traffichub_app` показал очистку `autolead_app_log` в 12:44:56.
- `/api/jobs/status` в таком состоянии возвращает `idle` без `job_id` и без `finished_at`.
- `dashboard/app.js::isConfirmedRealtimeTerminal()` до фикса не считал такой `idle` подтверждённым терминальным состоянием, если в `LAST_ACTIVE_JOB_STATUS` ещё лежала старая active job.

### Вывод

Root cause был во frontend guardrail: UI требовал `finished_at` для удаления active spinner, но после очистки логов/рестарта/пустой очереди канонический сигнал завершения может быть просто `status=idle` без `job_id`.

### Фикс

- Product commit `1b3030124`: `syncRealtimeJobSpinner()` сразу удаляет spinner при `status=idle` и пустом `job_id`.
- `isConfirmedRealtimeTerminal()` считает `idle` без `job_id` подтверждённым терминальным состоянием.
- Regression test: `tests/test_dashboard_realtime_spinner.py::test_idle_status_without_job_id_removes_stale_spinner_immediately`.
- Live deploy: `traffichub_app` перезапущен, `/api/health` вернул `status=ok`.
