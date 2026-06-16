# 2026-06-14 Heartbeat статус задачи мигал как transient spinner

## Симптом

- Пользователь видел строку вида `Полный цикл выполняется` с синим кружком.
- Строка появлялась на мгновение и сразу пропадала.
- Визуально это выглядело как отсутствие нормального realtime-лога с временем, хотя heartbeat фактически шел.

## Зона системы

- Live code:
  - `/root/TrafficHub/api/server.py`
  - `/root/TrafficHub/dashboard/app.js`
  - `/root/TrafficHub/utils/database.py`

## Гипотеза

- Статус задачи не терялся на backend.
- Он сохранялся в persistent `app_log`, но frontend рендерил heartbeat как transient spinner-строку и заменял её следующими сообщениями.

## Проверка

- В live code подтверждено:
  - `api/server.py::_push_status_loop()` создавал heartbeat:
    - `msg = "[i] Полный цикл: выполняется"`
    - `append_app_log(..., spinner=False, ...)`
    - `ws_manager.broadcast_log(..., spinner=True, ...)`
  - `dashboard/app.js::normalizeLogEntry()` дополнительно сам превращал текст
    - `Выгрузка выполняется`
    - `Рассылка выполняется`
    - `Полный цикл выполняется`
    в spinner даже без явного желания backend.
  - `dashboard/app.js::appendLog()` рендерил spinner в единственный DOM-элемент `.log-spinner`, который потом удалялся или заменялся.
- По live runtime в `/app/data/runtime/autolead.db` подтверждено:
  - heartbeat уже сохранялся как обычный persistent log с timestamp.
  - Примеры:
    - `2026-06-14 17:45:31 [i] Полный цикл: выполняется`
    - `2026-06-14 17:45:47 [i] Полный цикл: выполняется`
    - `2026-06-14 17:46:03 [i] Полный цикл: выполняется`
- Следствие:
  - backend-хранилище времени не теряло;
  - bug был именно в live UI-rendering websocket heartbeat.

## Наблюдение

- Это не проблема отсутствия timestamp в данных.
- Это не проблема фильтра `_is_dashboard_log_visible()`.
- Это UI/transport mismatch:
  - persistent storage считает heartbeat обычной строкой;
  - websocket/live UI трактовал heartbeat как временную анимацию.
- После нормального rebuild/restart `autolead_bot + worker` факт подтверждён повторно на debug owner `debug-worker-a`:
  - `2026-06-14 19:35:47 [i] Полный цикл: в очереди`
  - `2026-06-14 19:35:48 [i] Полный цикл: запущен`
  - `2026-06-14 19:35:49 [i] Полный цикл: выполняется`
  - `2026-06-14 19:35:49 [OK] Полный цикл: завершён`
- Все строки лежали в `app_log` с `spinner=0`, то есть после rebuild/restart heartbeat подтверждён уже не только source-code inspection, но и реальным runtime.
- Дополнительный post-restart runtime proof по боевым owner:
  - `admin`
    - `2026-06-14 14:40:30 [i] Полный цикл: выполняется`
    - `2026-06-14 14:40:33 [OK] Полный цикл: завершён`
  - `alex`
    - `2026-06-14 19:31:16 [i] Полный цикл: выполняется`
    - `2026-06-14 19:31:32 [i] Полный цикл: выполняется`
    - `2026-06-14 19:33:23 [i] Полный цикл: остановка`
  - `artem`
    - `2026-06-14 19:44:23 [i] Полный цикл: в очереди`
    - `2026-06-14 19:44:23 [i] Полный цикл: запущен`
    - `2026-06-14 19:44:25 [i] Полный цикл: выполняется`
    - `2026-06-14 19:44:28 [⛔] Полный цикл: остановлен`
- Во всех этих строках `spinner=0`.

## Вывод

- На `2026-06-14` исправление внесено в двух слоях:
  - в source tree `api/server.py` heartbeat websocket больше не должен идти как `spinner=True`;
  - в live `dashboard/app.js` heartbeat-строки
    - `Выгрузка выполняется`
    - `Рассылка выполняется`
    - `Полный цикл выполняется`
    больше не считаются transient spinner даже если старый backend ещё прислал `spinner=true`.
- Hotfix фронта был залит прямо в live container filesystem без рестарта боевых задач:
  - `autolead_server_bot:/app/dashboard/app.js`

## Обновление 2026-06-14 22:xx MSK

- Канон логов ещё раз изменён после runtime-проверки:
  - heartbeat больше не должен записываться в persistent `app_log` вообще;
  - realtime-статус должен собираться на клиенте из owner-scoped `status` websocket/poll, а не из server-side log spam.
- Подтверждённый live fix:
  - `/root/TrafficHub/api/server.py`
    - `_push_status_loop()` теперь только шлёт `broadcast_status(...)`;
    - `append_app_log(...)` и `broadcast_log(...)` из heartbeat-path убраны.
  - `/root/TrafficHub/dashboard/app.js`
    - добавлены `currentMoscowTimestamp()` и `syncRealtimeJobSpinner(data)`;
    - при `running/stopping` UI держит одну живую строку со временем слева;
    - old history heartbeat-pattern теперь фильтруется как шум.
  - `/root/TrafficHub/dashboard/style.css`
    - возвращена мягкая анимация `logPulse/logRipple` для активной строки;
    - `stopping` остаётся красным, а не синим.

## Обновлённый вывод

- История и realtime теперь разведены:
  - история хранит только важные завершённые события;
  - realtime статус живёт в одной анимированной строке и не засоряет `app_log`.
- Это ближе к требованию оператора:
  - видно, что задача жива;
  - слева есть время;
  - после завершения лента не захламляется heartbeat-дубликатами.

## Обновление 2026-06-15 01:xx MSK

### Симптом

- После предыдущих фиксов пользователь всё ещё видел краткую вспышку строки `Полный цикл выполняется`.
- В публичном UI слева у строк по-прежнему оставался пустой столбец времени.

### Проверка

- На live server подтверждено, что transient-строку продолжал создавать не `api/server.py`, а `utils/runtime_logging.py::StdoutToLogger.write()`:
  - carriage-return вывод (`"\r"`) логировался как `extra={"spinner": True}`;
  - это создавало websocket log-entry с `spinner=true`, который жил как кратковременная DOM-строка.
- На live server подтверждено расхождение между source tree и public runtime:
  - `/root/TrafficHub/dashboard/app.js` уже содержал fallback
    - `const effectiveTs = String(merged.ts || '').trim() || currentMoscowTimestamp();`
  - но `https://traffic-hubcrm.ru/app.js` продолжал отдавать старую версию из `autolead_server_bot`, где оставалось:
    - `tsShort: compactLogTime(merged.ts || '')`

### Наблюдение

- То есть оставалось два разных дефекта:
  - backend-source дефект: `stdout` progress still emitted transient spinner;
  - deploy/runtime дефект: public container served stale `app.js`.
- После hotfix:
  - `utils/runtime_logging.py`
    - carriage-return progress больше не пишет ничего в UI-log;
  - `dashboard/app.js`
    - timestamp fallback принудительно рисует время даже для старых/дефектных payload без `ts`;
  - `autolead_server_bot`
    - получил обновлённый `dashboard/app.js` через `docker cp` и restart.

### Вывод

- Канон на `2026-06-15`:
  - transient heartbeat/spinner нельзя генерировать из `stdout` carriage-return;
  - правка `dashboard/app.js` недостаточна сама по себе, пока asset не синхронизирован внутрь live container, который реально раздаёт `/app.js`.

## Следующий шаг

- После завершения активных user-run сделать нормальное применение source tree через rebuild/restart:
  - `autolead_bot`
  - `worker`
- Нормальный rebuild/restart уже выполнен на `2026-06-14`; transient heartbeat поведение не должно возвращаться после последующих рестартов, если не появится новый regression в `api/server.py` или `dashboard/app.js`.
