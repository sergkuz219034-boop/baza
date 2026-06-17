# Wave 4 execution pack: run status truthfulness

Дата: 2026-06-01

Связанные документы:
- [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
- [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)
- [2026-06-01 patch-plan run status and retry queue.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20run%20status%20and%20retry%20queue.md)
- [2026-06-01 run status and retry queue root causes.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20run%20status%20and%20retry%20queue%20root%20causes.md)

## Анализ

Этот execution-pack покрывает `Wave 4`: сделать итоговый статус цикла честным и фазово-осмысленным.

Подтверждённые факты по текущему snapshot:

- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:519)
  - `upload_sheets(...)` возвращает только `int`
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:826)
  - `run_full_cycle(...)` трактует результат только как `stats["sheets_added"]`
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:932)
  - `finish_run(..., status="ok")` вызывается безусловно
- [utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py:891)
  - `finish_run(...)` просто сохраняет переданный status

Дополнительные call sites:

- `upload_sheets(...)` зовётся ещё в:
  - [api/routers/jobs.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/routers/jobs.py:140)

Подтверждённые consumers статуса:

- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:752)
  - `run_statistics(...)` читает `get_recent_runs(10)`
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:773)
  - icon mapping сейчас такой:
    - `ok` -> `✅`
    - `running` -> `⚠️`
    - всё остальное -> `❌`

Вывод:
- новые статусы не обязаны ломать код статистики;
- но UI/операторская интерпретация изменится, и это нужно считать ожидаемым side effect.

## Причина

### 1. Контракт `upload_sheets()` слишком бедный

Сейчас:
- `0` означает и “нет новых строк”, и “фаза упала”

Это делает невозможным честный `run_status`.

### 2. `run_full_cycle()` не хранит фазовый outcome

Сейчас:
- нет `phase_failures`
- нет `phase_status`
- нет вычисления итогового статуса по результатам фаз

### 3. `run_log.status` пишется как `ok` без анализа результата

Это и порождает основной пользовательский симптом:
- timeout в Sheets
- но итог всё равно выглядит успешным

## План исправления

### Шаг 1. Расширить контракт `upload_sheets()`

Рекомендуемый переходный контракт:

```diff
- def upload_sheets(config: dict, leads: list) -> int:
+ def upload_sheets(config: dict, leads: list) -> dict:
```

Рекомендуемый shape:

```python
{"added": int, "failed": bool, "reason": str | None}
```

### Шаг 2. Адаптировать оба call sites

Нужно обновить:
- `run_full_cycle(...)`
- `api/routers/jobs.py` upload-команду

### Шаг 3. Ввести phase-failure tracking в `run_full_cycle()`

Минимально:

```python
phase_failures: list[dict] = []
```

И при проблеме Sheets:

```python
phase_failures.append({"phase": "sheets", "reason": "upload_error"})
```

### Шаг 4. Вычислять итоговый `run_status`

Рекомендуемая переходная логика:

- `stopped`, если сработал `/stop`
- `failed`, если есть phase failures и полезный результат цикла не достигнут
- `partial_failure`, если часть работы выполнена, но есть фазовая деградация
- `ok`, если phase failures нет

## Diff

### 1. `upload_sheets()`

```diff
# remote_server_snapshot/services/leads_service.py
- def upload_sheets(config: dict, leads: list) -> int:
+ def upload_sheets(config: dict, leads: list) -> dict:
```

```diff
- return 0
+ return {"added": 0, "failed": False, "reason": None}
```

для нормального “выключено” или “остановлено”, если это не считать ошибкой фазы.

```diff
- return added
+ return {"added": added, "failed": False, "reason": None}
```

```diff
- return 0
+ return {"added": 0, "failed": True, "reason": "upload_error"}
```

### 2. `run_full_cycle()`

```diff
- stats = {"leads_found": 0, "sheets_added": 0, "sent": 0,
-          "skipped": 0, "errors": 0, "duplicates": 0, "retried": 0}
+ stats = {"leads_found": 0, "sheets_added": 0, "sent": 0,
+          "skipped": 0, "errors": 0, "duplicates": 0, "retried": 0}
+ phase_failures = []
```

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
+ if phase_failures and stats.get("sent", 0) == 0:
+     run_status = "failed"
+ elif phase_failures:
+     run_status = "partial_failure"
```

### 3. `api/routers/jobs.py`

Upload-команда сейчас игнорирует richer result:

```diff
- leads_service.upload_sheets(config, leads)
+ sheets_result = leads_service.upload_sheets(config, leads)
+ if sheets_result.get("failed"):
+     logger.warning("upload: sheets phase failed: %s", sheets_result.get("reason"))
```

Даже если upload job не пишет run_log, richer result всё равно нельзя silently терять.

## Почему это безопасно

1. Изменение локализовано:
- `upload_sheets`
- `run_full_cycle`
- `jobs.py` upload path

2. `run_statistics()` уже не требует строго двух статусов:
- всё кроме `ok` и `running` он и так показывает как problem-state

3. Изменение не требует немедленной миграции БД:
- `run_log.status` уже string field

## Побочные эффекты

### Ожидаемые

- часть прошлых запусков и новые запуски начнут показываться как `❌`, где раньше были `✅`
- это не регрессия, а исправление observability

### Возможные скрытые

- если внешний UI жёстко ожидает только `ok/running/stopped`, новые статусы нужно будет проверить end-to-end

## Проверка после исправления

### Обязательные проверки

1. Timeout Google Sheets:
- даёт `failed` или `partial_failure`
- не заканчивается как `ok`

2. Normal zero-add upload:
- если ошибок не было, остаётся `ok`

3. `/stop` path:
- остаётся `stopped`

4. `run_statistics()`:
- корректно показывает новые problem-states

5. Upload job path:
- не теряет richer result бесследно

## Открытый вопрос

Нужно продуктово уточнить границу между:

- `failed`
- `partial_failure`

На текущем уровне безопасное правило:
- если phase failure есть и полезный результат цикла фактически нулевой, считать `failed`
- если часть полезной работы всё же завершена, считать `partial_failure`
