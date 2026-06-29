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
