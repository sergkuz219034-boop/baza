# 2026-06-28 Full cycle realtime spinner flicker

## Симптом

- В live UI строка `Полный цикл: выполняется` мерцает во время активной задачи.
- Пользователь воспринимает это как повторное появление/исчезновение строки логов.

## Зона системы

- Frontend log terminal: `/root/TrafficHub/dashboard/app.js`.
- Realtime job status: `syncRealtimeJobSpinner()`.
- Общий pipeline логов: `appendLog()`.

## Гипотеза

- Realtime-строка полного цикла обновлялась через общий `appendLog(... spinner: true)` pipeline.
- При каждом тике статуса строка могла проходить через общий механизм логов и DOM-поиск по `.log-spinner`, из-за чего элемент визуально пересоздавался или конфликтовал с историческими логами.

## Проверка

- Проверен live-код `/root/TrafficHub/dashboard/app.js`.
- До фикса `syncRealtimeJobSpinner()` вызывал `appendLog({ ..., spinner: true }, true)`.
- `appendLog()` имел отдельную ветку для `spinner`, но не использовал стабильный id строки и оставался связан с общим log pipeline.

## Наблюдение

- Runtime-строка `Полный цикл: выполняется` не является исторической записью лога.
- Она должна быть временным статусом активной задачи и обновляться in-place.
- Исторические строки (`Полный цикл завершён`, `Полный цикл остановлен`, ошибки офферов) должны оставаться обычными логами.

## Вывод

- Причина мерцания: realtime status row была реализована как особый случай внутри общего log pipeline.
- Надёжный контракт: для активной задачи существует ровно один DOM-элемент `#realtime-job-spinner`, который обновляет только `time` и `text`, но не пересоздаётся каждую секунду.

## Исправление

- Product commit: `6c45c0850 fix: keep full cycle status row stable`.
- Добавлены функции:
  - `ensureRealtimeSpinnerLine()`
  - `updateRealtimeSpinnerLine(entry)`
- `syncRealtimeJobSpinner()` больше не вызывает `appendLog()` для spinner-строки.
- `appendLog()` при `normalized.spinner` только обновляет стабильную строку и сразу выходит.
- Добавлен regression test: `/root/TrafficHub/tests/test_dashboard_realtime_spinner.py`.

## Проверка после фикса

- `node --check dashboard/app.js` — passed.
- `python -m pytest tests/test_dashboard_realtime_spinner.py tests/test_dashboard_encoding.py tests/test_runtime_logging.py -q` — `6 passed`.
- `docker compose up -d --build autolead_bot worker` — контейнеры пересозданы.
- `https://traffic-hub.pro/api/health` — `status=ok`.
- В live `app.js` подтверждены `REALTIME_SPINNER_ID`, `ensureRealtimeSpinnerLine`, `updateRealtimeSpinnerLine`.
- `maintenance_mode=False`.

## Следующий шаг

- Для любых будущих live-status строк не использовать `appendLog()` как источник истины UI-состояния.
- Исторический лог и realtime status должны быть разными слоями.
