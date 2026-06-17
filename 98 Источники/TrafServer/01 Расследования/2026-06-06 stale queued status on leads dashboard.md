# 2026-06-06 stale queued status on leads dashboard

## Симптом

На экране `/#leads` статус в header зависал в `В ОЧЕРЕДИ`, хотя worker не выполнял задачи и активной очереди не было.

## Зона

- `dashboard/app.js`
- `api/ws_manager.py`
- `traffic_hub.services.job_queue`

## Гипотеза

Фронтенд получает не реальный текущий status, а устаревший snapshot из websocket-менеджера.

## Проверка

1. Проверен `traffichub_worker`: активных owner в `job_queue.list_active_owners()` нет.
2. Проверен `autolead_server_bot`: `job_queue.get_job_status("sergey")` возвращает `idle`.
3. Прочитан `api/ws_manager.py`: `connect_status()` при новом подключении отправляет `_last_status`, а не `job_queue.get_job_status(owner)`.
4. Прочитан `dashboard/app.js`: `connectStatusWs()` не делает стартовый `refreshJobStatus()` после открытия websocket.

## Наблюдение

- `_last_status` в `WSManager` глобальный и может пережить прошлый `queued/running` event.
- Если новых событий не приходит, UI остаётся на старом badge.
- Worker и queue backend при этом могут быть уже пустыми.

## Вывод

Первопричина была в bootstrap-логике статуса:

- сервер при подключении websocket не сверялся с реальным `job_queue` для пользователя;
- фронтенд не запрашивал актуальный status после открытия `ws/status`.

## Что исправлено

На сервере:

- `api/ws_manager.py`
  - `connect_status()` теперь сначала отправляет `job_queue.get_job_status(owner)` для конкретного пользователя;
  - fallback на `_last_status` оставлен только как запасной путь.
- `dashboard/app.js`
  - `connectStatusWs()` теперь вызывает `refreshJobStatus()` в `onopen`.

## Результат

После пересборки `autolead_server_bot`:

- контейнер `healthy`;
- `job_queue.get_job_status("sergey")` возвращает `idle`;
- stale `queued` больше не должен залипать после reload/reconnect.
