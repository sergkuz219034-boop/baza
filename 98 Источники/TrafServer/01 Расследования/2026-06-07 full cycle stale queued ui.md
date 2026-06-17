# Full Cycle не запускался из-за stale `queued` в UI

## Симптом

На странице `/#leads` кнопка `Полный цикл` оставалась неактивной, а header-status показывал `В ОЧЕРЕДИ`, хотя реальная очередь уже была свободна.

## Зона системы

- `dashboard/app.js`
- `api/ws_manager.py`
- `traffic_hub/services/job_queue.py`
- Redis keys `traffic_hub:jobs:state:*`

## Гипотеза

Клиентский UI держал устаревший job-status и не перепроверял его достаточно агрессивно после reconnect/неудачного websocket snapshot.

## Проверка

- В Redis для `artem` состояние было `idle`, очередь `traffic_hub:jobs:queue` была пустой.
- Worker `traffichub_worker` был жив и не держал активный job.
- В браузерный `dashboard/app.js` встроено блокирование кнопок через `JOB_BUSY` / `JOB_START_PENDING`.
- Статус обновлялся в основном через websocket `/ws/status`; HTTP refresh был недостаточно надёжным fallback.

## Наблюдение

Серверный runtime был свободен, но клиент мог залипнуть в старом `queued` и не разблокировать action buttons.

## Решение

В `dashboard/app.js` на сервере добавлено:

- обязательный `refreshJobStatus()` при старте приложения;
- polling fallback каждые 5 секунд, если websocket недоступен или оборвался;
- снятие `JOB_START_PENDING` при неудачном `refreshJobStatus()`.

## Вывод

Проблема была не в `run_full_cycle()` и не в worker execution path, а в stale UI-state вокруг статуса очереди.

## Следующий шаг

- если симптом повторится, смотреть сначала `Redis state`, потом `/api/jobs/status`, и только потом уже сам worker.
