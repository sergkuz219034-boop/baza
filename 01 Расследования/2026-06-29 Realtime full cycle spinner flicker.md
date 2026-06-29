# 2026-06-29 Realtime full cycle spinner flicker

## Симптом

В UI строка realtime-статуса вида `Полный цикл: выполняется` мигала/дёргалась во время работы задачи.

## Зона системы

- `dashboard/app.js`
- websocket `/ws/status`
- fallback `refreshJobStatus()` polling

## Гипотеза

Проблема не в тексте строки, а в гонке между несколькими источниками статуса:

- websocket snapshot;
- HTTP refresh;
- локальный секундный ticker для elapsed-time.

Если один из промежуточных snapshot'ов на короткий момент отдаёт не `running`, spinner-строка удаляется и тут же рисуется заново.

## Проверка

1. Проверен live `dashboard/app.js`.
2. Подтверждено, что realtime-строка обновляется через `syncRealtimeJobSpinner(data)`.
3. До фикса логика сразу удаляла строку при любом статусе вне `queued/running`.
4. Добавлен grace-period удаления:
   - новый `realtimeSpinnerRemovalTimer`;
   - `stopping` считается активным transitional статусом;
   - удаление spinner-строки теперь откладывается на `2500 ms`;
   - если за это время приходит новый `queued/running/stopping`, удаление отменяется.
5. Обновлённый `dashboard/app.js` подложен в `traffichub_app`.
6. `api/health` внутри контейнера отвечает `ok`.

## Наблюдение

- В live-файле уже была более аккуратная реализация `updateRealtimeSpinnerLine()` без полного `innerHTML` repaint.
- Оставшийся дефект был именно в слишком агрессивном remove-path, а не в render-path.

## Вывод

Первопричина мигания — кратковременные статусные провалы между WS и HTTP snapshot'ами.

Исправление: spinner больше не исчезает мгновенно на промежуточном статусе и переживает короткие race-condition окна.

## Следующий шаг

- Проверить на реальном `Полный цикл`, что строка больше не мигает визуально.
- Если симптом повторится, следующая зона — серверный источник `/api/jobs/status` и порядок публикации событий в `ws/status`.

## Дополнительная проверка 2026-06-29

Симптом повторился после первого grace-period фикса. Повторная проверка live-кода показала ещё три источника визуального мигания:

1. `loadLogSnapshot()` вызывал `clearLocalLog()` и полностью чистил `#log-body` при фоновой загрузке истории.
2. `clearLocalLog()` сбрасывал `LAST_JOB_STATUS` и останавливал realtime ticker даже для фонового snapshot reload.
3. `syncRealtimeJobSpinner()` запускал секундный ticker, который сам перерисовывал timestamp строки каждую секунду.

Также на сервере `api/ws_manager.py::connect_status()` сначала мог отдавать `_last_status`, а только потом fallback на `job_queue.get_job_status(owner)`. При reconnect это оставляло окно для устаревшего snapshot.

## Дополнительное решение 2026-06-29

Фронтенд:

- `loadLogSnapshot()` теперь вызывает `clearLocalLog({ preserveRealtimeStatus: true })`.
- `clearLocalLog()` получил режим сохранения realtime-строки: чистит исторические строки, но не удаляет `#realtime-job-spinner`.
- При preserve-режиме `LAST_JOB_STATUS` не сбрасывается.
- `syncRealtimeJobSpinner()` больше не запускает секундный ticker, поэтому строка `Полный цикл: выполняется` не перерисовывается сама по себе каждую секунду.

Backend:

- `api/ws_manager.py::connect_status()` теперь сначала отправляет `job_queue.get_job_status(owner)` для owner-scoped подключения.
- `_last_status` оставлен только как fallback, если актуальный owner status недоступен.

Проверка:

- `node --check` для обновлённого `dashboard/app.js` прошёл.
- `py_compile` для обновлённого `api/ws_manager.py` прошёл через `/tmp/ws_manager.pyc`.
- Файлы подложены в `traffichub_app`.
- `api/health` внутри контейнера вернул `status=ok`.
- Контейнерная проверка подтвердила:
  - `noTickerCallInSpinner=True`
  - `preserveRealtimeStatus=True`
  - `softSnapshotClear=True`

## Финальная проверка 2026-06-29

Повторная контейнерная проверка после деплоя показала, что старый локальный repaint-механизм удалён полностью:

- в `/app/dashboard/app.js` больше нет `realtimeSpinnerTimer`;
- в `/app/dashboard/app.js` больше нет `ensureRealtimeSpinnerTicker()`;
- внутри `syncRealtimeJobSpinner()` больше нет `setInterval`;
- неактивный статус больше не удаляет строку мгновенно, а идёт через `scheduleRealtimeSpinnerRemoval()`;
- `loadLogSnapshot()` использует `clearLocalLog({ preserveRealtimeStatus: true })`;
- `/app/api/ws_manager.py` при owner-scoped reconnect сначала отдаёт `job_queue.get_job_status(owner)`, а `_last_status` использует только как fallback.

Health контейнера:

- `/api/health` вернул `{"status":"ok","version":"1.2","app":"TrafficHub"}`.

Вывод: подтверждённые источники мигания `Полный цикл: выполняется` закрыты на уровне frontend repaint, log snapshot clear и websocket reconnect snapshot. Остаточный риск — только визуальная проверка в браузере на следующем полном цикле после обновления страницы.

## Поведенческая регрессия 2026-06-29

Дополнительно выполнена Node-проверка на живом `/root/TrafficHub/dashboard/app.js` с минимальной DOM-моделью. Смоделирован сценарий, который раньше вызывал мигание:

1. `syncRealtimeJobSpinner(running)`;
2. `clearLocalLog({ preserveRealtimeStatus: true })`;
3. краткий `syncRealtimeJobSpinner(idle)`;
4. повторный `syncRealtimeJobSpinner(running)`.

Результат:

- `stableSameNode=true` — DOM-узел `#realtime-job-spinner` остался тем же самым;
- `removeCount=0` — строка не удалялась;
- `pendingTimers=0` — таймер отложенного удаления отменился после возврата `running`;
- новый spinner subtree не создавался после первого render.

Вывод: зафиксирована не только структура кода, но и поведение против основного race-condition сценария `running -> snapshot/status gap -> running`.

## Headless Chrome проверка 2026-06-29

Через SSH-туннель открыт реальный TrafficHub dashboard (`http://127.0.0.1:18080/`) в headless Chrome. Через DevTools Protocol дождались загрузки `app.js` и выполнили тот же сценарий уже в настоящей странице:

- `syncRealtimeJobSpinner(running)`;
- `clearLocalLog({ preserveRealtimeStatus: true })`;
- краткий `syncRealtimeJobSpinner(idle)`;
- повторный `syncRealtimeJobSpinner(running)`.

Результат браузерной проверки:

- `ok=true`;
- `sameAfterClear=true`;
- `sameAfterIdle=true`;
- `sameAfterReturn=true`;
- `removes=0`;
- `spinnerCount=1`;
- итоговый текст строки: `Полный цикл выполняется`;
- класс строки: `log-line INFO log-spinner`.

Вывод: на реальной странице подтверждено, что основной сценарий мигания больше не удаляет и не пересоздаёт строку `Полный цикл выполняется`.

## Зависание вида "ничего не происходит" 2026-06-29

### Симптом

В UI после запуска полного цикла отображались только строки:

- `Фаза 1: Сбор лидов с Rabota.ru`;
- `Полный цикл выполняется`.

Дальше консоль визуально не обновлялась, хотя задача продолжала работать.

### Зона системы

- `utils/runtime_logging.py`
- `traffic_hub/services/job_runner.py`
- `traffic_hub/worker.py`
- таблица `autolead_app_log`
- websocket/log bridge dashboard

### Гипотеза

Рабочий процесс не зависал. Прогресс был в stdout worker-контейнера, но не попадал в owner-scoped UI log из-за фильтра релевантности логов.

### Проверка

Проверен live-runtime на сервере:

- контейнеры `traffichub_app`, `traffichub_worker`, `traffichub_postgres`, `traffichub_redis` были healthy;
- worker stdout показывал прогресс Rabota.ru: API-запросы, загрузку откликов, итог уникальных откликов;
- `autolead_app_log` после очистки содержал только стартовые строки и не содержал прогресса загрузки.

Проверен `utils/runtime_logging.py`: в `_UI_DROP_REGEXES` были правила, которые отбрасывали полезные строки:

- `[API] ...`;
- `[i] Rabota.ru: ...`;
- `⠋ Загрузка ...`;
- `✓ Загрузка ...`.

### Наблюдение

Фильтр UI-логов выполнялся до keep-правил, поэтому рабочие строки Rabota.ru удалялись до записи в persistent log и до live-вывода в dashboard.

### Вывод

Первопричина симптома — не зависание полного цикла, а слишком агрессивный фильтр `utils/runtime_logging.py`.

На сервере исправлено:

- `[API] ...` больше не отбрасывается;
- `[i] Rabota.ru: ...` больше не отбрасывается;
- строки `⠋ Загрузка ...` и `✓ Загрузка ...` считаются релевантными для UI;
- контейнеры `autolead_bot` и `worker` пересобраны и перезапущены;
- проверка `is_ui_relevant_log()` подтвердила `True` для API, прогресса загрузки и итоговой строки Rabota.ru.

Кодовый commit: `2c4149c78 Show Rabota progress logs in dashboard`.

### Следующий шаг

При следующем запуске полного цикла UI должен показывать не только фазу 1, но и рабочие строки загрузки Rabota.ru. Если снова будет визуальная пауза, проверять уже источник событий job runner, а не только frontend.
