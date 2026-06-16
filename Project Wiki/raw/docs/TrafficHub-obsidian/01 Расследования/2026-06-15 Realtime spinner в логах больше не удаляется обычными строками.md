# Realtime spinner в логах больше не удаляется обычными строками

## Симптом

Во время запуска `Полный цикл` / `Выгрузка` / `Рассылка` строка живого статуса появлялась на секунду и исчезала. При нажатии `Стоп` UI не всегда сразу переходил в состояние остановки.

## Зона системы

- `dashboard/app.js`
- `api/routers/jobs.py`
- `traffic_hub/services/job_queue.py`
- `api/server.py`

## Гипотеза

Проблема была не в owner-scoped queue, а в frontend-отрисовке:

- `syncRealtimeJobSpinner()` очищал spinner и не рисовал его для `queued/running`;
- `appendLog()` удалял `.log-spinner` при любой обычной log-строке;
- `stopJob()` не делал немедленный `refreshJobStatus()`.

## Проверка

- inspected live `dashboard/app.js`
- inspected live `api/routers/jobs.py`
- inspected live `traffic_hub/services/job_queue.py`
- synthetic runtime check inside container:
  - `enqueue_job('debuglogs', 'run')`
  - `request_stop_for_job('debuglogs')`

## Наблюдение

- server-side stop path уже был мгновенным:
  - `STATUS1 queued run`
  - `STATUS2 stopping run`
  - `STATUS3 stopping run`
- то есть backend сразу переводит job в `stopping`
- live frontend fixes на `2026-06-15`:
  - `syncRealtimeJobSpinner()` теперь держит spinner для `queued`, `running`, `stopping`
  - spinner-строка получает timestamp слева через `currentMoscowTimestamp()`
  - при `stopping` строка создаётся с `level='ERROR'`
  - `appendLog()` больше не удаляет spinner обычной строкой; новые строки вставляются перед ним
  - `stopJob()` теперь после POST `/api/jobs/stop` сразу вызывает `refreshJobStatus()`

## Вывод

Мигание status-line было frontend-багом, а не дефектом Redis queue или worker stop-state. Канонический server stop-state остаётся owner-scoped и мгновенно меняется на `stopping`.

## Следующий шаг

- проверить live UI в браузере на реальном owner job;
- если spinner всё ещё “дёргается”, искать уже не удаление строки, а конфликт между auto-scroll и повторным render одной и той же spinner-записи.
