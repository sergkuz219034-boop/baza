# Run status and retry queue root causes

Дата: 2026-06-01

Связанные материалы:
- [2026-06-01 autolead 3 log analysis.md](C:/Users/Арт/Desktop/TrafServer/01%20Расследования/2026-06-01%20autolead%203%20log%20analysis.md)
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py)
- [utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py)

## Анализ

Подтверждены две связанные первопричины в текущем run/retry lifecycle.

1. Ошибка выгрузки в Google Sheets не поднимается до run-level статуса.
2. Retry queue не умеет корректно завершать terminal skip-сценарии.

Это подтверждено одновременно:
- реальным логом `autolead (3).log`
- текущим кодом `remote_server_snapshot`

## Причина

### 1. Phase failure в Sheets маскируется под обычный `0`

- `upload_sheets(config, leads)` ловит исключение и возвращает `0`
- `run_full_cycle(config, period)` записывает это только как:
  - `stats["sheets_added"] = added`
- отдельного phase outcome нет
- в конце `run_full_cycle(...)` всегда вызывает:
  - `finish_run(run_id, stats, status="ok")`

Итог:
- timeout в Google Sheets не переводит run в `failed` или `partial_failure`
- оператор видит:
  - `Sheets: 0`
  - `Ошибок: 0`

### 2. Retry queue не завершает terminal `missing offer` сценарии

- `process_retry_queue(config)` получает due retries
- затем прогоняет каждую запись через `run_sender(...)`
- при terminal skip:
  - запись не удаляется из `retry_queue`
  - `retry_count` не увеличивается
  - `next_retry_at` не меняется

Удаление есть только в двух случаях:
- запись уже присутствует в `send_history`
- downstream-логика когда-то сама довела её до sent/duplicate

Итог:
- записи, которые стабильно дают `SKIP` из-за отсутствующего offer/vacancy mapping, могут снова и снова попадать в обработку
- это создаёт бесконечный operational noise и искажает картину retry health

## Критичность

### Проблема 1. Ложный `ok` при провале Sheets phase
- Критичность: `High`
- Последствия:
  - ложная observability
  - run_log врёт о состоянии цикла
  - операторы и мониторинг пропускают фактический сбой фазы

### Проблема 2. Застревающие terminal retry items
- Критичность: `Medium`
- Последствия:
  - бесконечный шум в логах
  - повторная бессмысленная обработка
  - раздутая retry queue
  - ухудшение качества operational диагностики

## Рекомендуемое исправление

### Для run-level статуса

- разделить в `upload_sheets()`:
  - `success with 0 rows`
  - `phase failure`
- передавать в `run_full_cycle()` фазовый outcome, а не только integer count
- завершать `run_log` статусами:
  - `ok`
  - `partial_failure`
  - `failed`
  - `stopped`

### Для retry queue

- ввести terminal reason для случаев вроде:
  - `missing_offer_mapping`
- при таком исходе:
  - либо удалять запись из `retry_queue`
  - либо архивировать её в отдельный terminal store
- не оставлять terminal skip в бесконечном цикле `due_retries`

## Patch direction

Минимальный безопасный путь:

1. Не ломать текущий контракт `stats`.
2. Добавить отдельный phase flag для Sheets.
3. Вычислять итоговый `run_status` в `run_full_cycle(...)` перед `finish_run(...)`.
4. Добавить для retry queue явную terminal classification, не смешанную с временными retryable исходами.
