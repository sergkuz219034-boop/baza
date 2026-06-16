# Логи UI как короткая owner-scoped лента

## Проблема

- Пользовательский live-log был либо слишком техническим, либо визуально создавал ощущение зависания.
- Backend и frontend исторически писали много промежуточных строк:
  - `Sheets upload`
  - `Retry queue`
  - `-> Заполняем`
  - системные heartbeat/counters

## Контекст

- Live runtime использует owner-scoped queue и owner-scoped log delivery:
  - `api/ws_manager.py`
  - `api/server.py`
  - `traffic_hub/services/job_queue.py`
- Пользователю нужен не raw trace, а компактная рабочая лента:
  - статус задачи в реальном времени;
  - важные бизнес-события офферов;
  - ошибки.

## Решение

- Шум режется на двух уровнях:
  - backend:
    - `utils/runtime_logging.py`
    - `api/server.py`
  - frontend:
    - `dashboard/app.js`
- Для Playwright/navigation ошибок действует тройная защита:
  - sender-runtime сокращает raw exception;
  - `api/server.py` нормализует history/snapshot строки;
  - `dashboard/app.js` финально режет `Call log` и multiline при рендере.
- Heartbeat должен оставаться realtime, но не должен жить как persistent history.
- Канон после live-fix `2026-06-14`:
  - `api/server.py` отправляет owner-scoped `status`, а не heartbeat-строки в `app_log`;
  - `dashboard/app.js` сам строит одну живую строку `spinner` из `status`;
  - время этой строки рисуется слева на клиенте;
  - при `stopping` живая строка остаётся красной.
- Дополнительный live-fix `2026-06-15`:
  - `utils/runtime_logging.py::StdoutToLogger.write()` не должен превращать carriage-return progress в websocket `spinner=True`;
  - иначе UI получает transient-строку, которая мигает и пропадает;
  - после правки `dashboard/app.js` static asset должен быть синхронизирован именно в live container (`autolead_server_bot`), иначе public `/app.js` останется на старой версии даже при обновлённом source tree.
- Канонический пользовательский состав ленты:
  - `в очереди`
  - `запущен`
  - `выполняется`
  - `остановка`
  - `остановлен`
  - `завершён`
  - `[OK] Оффер ...`
  - `[~] Оффер ...`
  - `Ошибка ...`
- Автоскролл разрешён только в момент добавления новой строки.
- Перерисовка существующего spinner/status не должна сдвигать scroll position.
- Timestamp в UI-ленте не должен оставаться пустым даже при дефектном payload:
  - frontend использует fallback `currentMoscowTimestamp()` для строк без `ts`;
  - это runtime-защита, а не замена нормального server timestamp.

## Последствия

- Лента стала пригодной для оператора без чтения технических деталей runtime.
- Детальные counters, служебные переходы и вспомогательные строки должны оставаться в системных логах, а не в основной пользовательской ленте.
- Исторический `app_log` перестаёт раздуваться heartbeat-дубликатами каждые `~15s`.
- Любая новая backend-строка, попадающая в UI, должна считаться suspect, пока не доказано, что это business event, а не шум.
- Для sender/runtime это означает отдельное требование:
  - многострочные ошибки Playwright не должны попадать в UI в raw-виде;
  - runtime обязан отдавать сжатую формулировку ошибки до попадания в `app_log`.
- На live runtime 13.06.2026 это подтверждено фактом:
  - в сыром `app_log` ещё может лежать multiline `Page.goto ... Call log ...`;
  - но через `/api/logs` пользователь получает одну короткую строку ошибки без хвоста `Call log`.

## Альтернативы

- Показывать весь raw `app_log` в UI:
  - отвергнуто, потому что это превращает интерфейс в debug console.
- Полностью убрать heartbeat:
  - отвергнуто, потому что пользователь снова будет думать, что задача зависла.
