# Patch-plan: run status and retry queue

Дата: 2026-06-01

Связанные файлы:
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py)
- [utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py)
- [2026-06-01 run status and retry queue root causes.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20run%20status%20and%20retry%20queue%20root%20causes.md)

## Анализ

Ниже точечный patch-plan без применения.

Цель:
- перестать маркировать провал Sheets phase как `ok`
- перестать бесконечно гонять terminal retry items

## Причина

### 1. `upload_sheets()` возвращает слишком бедный результат

Сейчас:
- успех и неуспех схлопываются в один integer

Нужно:
- фазовый результат, достаточный для `run_full_cycle(...)`

### 2. `process_retry_queue()` не завершает terminal skip outcomes

Сейчас:
- запись может застрять в `retry_queue`

Нужно:
- явное завершение terminal исходов

## План исправления

1. В `upload_sheets()` вернуть не только `added`, но и outcome:
- вариант A: `tuple[int, bool]`
- вариант B: `dict`

Рекомендуемый безопасный вариант:
- `{"added": int, "failed": bool, "reason": str | None}`

2. В `run_full_cycle()`:
- сохранять `stats["sheets_added"]`
- отдельно держать `phase_failures`
- вычислять итоговый `run_status` перед `finish_run(...)`

3. В `process_retry_queue()`:
- детектировать terminal skip outcome
- на terminal outcome:
  - либо удалять запись из `retry_queue`
  - либо помечать как завершённую в отдельном store

Минимальный безопасный вариант:
- удалять из `retry_queue` при подтверждённом terminal `missing_offer_mapping`
- логировать отдельной строкой причину terminal removal

## Diff

### 1. Направление для `upload_sheets()`

```diff
- def upload_sheets(config: dict, leads: list) -> int:
+ def upload_sheets(config: dict, leads: list) -> dict:
```

```diff
- return added
+ return {"added": added, "failed": False, "reason": None}
```

```diff
- return 0
+ return {"added": 0, "failed": True, "reason": "upload_error"}
```

### 2. Направление для `run_full_cycle()`

```diff
- added = upload_sheets(config, leads)
- stats["sheets_added"] = added
+ sheets_result = upload_sheets(config, leads)
+ stats["sheets_added"] = sheets_result.get("added", 0)
+ if sheets_result.get("failed"):
+     phase_failures.append({"phase": "sheets", "reason": sheets_result.get("reason")})
```

```diff
- finish_run(run_id, stats, status="ok")
+ finish_run(run_id, stats, status=run_status)
```

Где:

```diff
+ run_status = "ok"
+ if is_stop_requested():
+     run_status = "stopped"
+ elif phase_failures and stats.get("sent", 0) == 0:
+     run_status = "failed"
+ elif phase_failures:
+     run_status = "partial_failure"
```

### 3. Направление для `process_retry_queue()`

```diff
+ terminal_reason = _classify_terminal_retry_outcome(retry_stats, item)
+ if terminal_reason == "missing_offer_mapping":
+     remove_from_retry_queue(phone, offer_name)
+     logger.info("process_retry_queue: terminal retry removed %s (%s)", history_key, terminal_reason)
+     continue
```

Если точной машинной классификации ещё нет, промежуточный вариант:
- добавить её в downstream `run_campaign(...)`
- возвращать reason через `lead_results`

## Риски

### Риск 1. Ломка текущего контракта `upload_sheets()`
- если функцию зовут ещё где-то кроме `run_full_cycle()` и `jobs.py`, потребуется синхронная адаптация call sites

### Риск 2. Неверная классификация terminal outcome
- если ошибочно считать временную проблему terminal, запись можно удалить слишком рано

### Риск 3. Изменение статусов run может затронуть UI/отчёты
- нужно проверить, кто читает `run_log.status`

## Проверка после исправления

1. Timeout Google Sheets даёт:
- `sheets_added = 0`
- `run_status != ok`

2. Успешный run без новых строк в Sheets даёт:
- `sheets_added = 0`
- `run_status = ok`

3. Retry item с terminal missing-offer больше не появляется в каждом цикле.

4. Обычные временные retryable ошибки продолжают жить в retry queue.

## Дополнительные улучшения

- Добавить в `run_log` отдельное поле `phase_failures_json`
- Добавить terminal retry audit table вместо простого удаления
- Добавить distinction между:
  - `skipped`
  - `duplicate`
  - `terminal`
  - `retryable_error`
