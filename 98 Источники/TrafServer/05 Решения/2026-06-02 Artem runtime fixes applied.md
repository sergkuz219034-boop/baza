# Artem: runtime fixes applied

Дата: 2026-06-02

Связанные документы:
- [2026-06-02 Artem full cycle upload and send root cause.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-02%20Artem%20full%20cycle%20upload%20and%20send%20root%20cause.md)
- [2026-06-02 Artem run no-op and settings wipe findings.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-02%20Artem%20run%20no-op%20and%20settings%20wipe%20findings.md)

## Анализ

Для инцидента `Artem` внедрены не только защитные правки UI/backend, но и runtime-исправления полного цикла.

На этом шаге закрыты три подтверждённые проблемы:

1. `upload_sheets()` больше не маскирует сбой как обычный `0`.
2. `run_full_cycle()` больше не обнуляет send-phase, если pending Sheets queue пустая или недоступна.
3. retry-path теперь перед отправкой добирает vacancy context из локальной `leads`-таблицы.

## Причина

### 1. Upload phase была ложноположительно “успешной”

- раньше `upload_sheets()` возвращал только `int`;
- timeout и нормальный нулевой результат выглядели одинаково.

### 2. Full cycle терял свежие лиды после неудачной выгрузки

- при `google_sheets.enabled=true` send-phase пыталась взять pending queue;
- если очередь пустая или недоступна, `all_leads_to_send` превращался в пустой список.

### 3. Retry lead был беднее обычного lead

- в retry path не хватало `Вакансия`, `Пол`, `Дата`;
- для `missing offer` это было сильным кандидатом на boundary bug перед sender.

## План исправления

Внедрён такой путь:

1. `upload_sheets()` возвращает структурированный результат.
2. `run_full_cycle()` умеет:
- помечать фазовые сбои;
- fallback на свежие лиды;
- fallback на локальный backlog, если нужно.
3. `process_retry_queue()` обогащает retry lead из `leads`.

## Diff

Изменены файлы:

- [remote_server_snapshot/services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py)
- [remote_server_snapshot/utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py)
- [remote_server_snapshot/api/routers/jobs.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/routers/jobs.py)
- [remote_files/services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py)
- [remote_files/utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/database.py)
- [remote_files/api/routers/jobs.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/jobs.py)

Ключевые изменения:

```diff
- def upload_sheets(...) -> int
+ def upload_sheets(...) -> dict
```

```diff
- pending queue empty -> all_leads_to_send = []
+ pending queue empty -> fallback to fresh leads or local backlog
```

```diff
+ get_latest_lead_context_by_phones(...)
+ retry lead enrichment: Вакансия / Пол / Дата / IDs
```

```diff
- finish_run(..., status="ok")
+ finish_run(..., status=run_status)
```

## Риски

1. Внешний timeout Google Sheets сам по себе этим не устранён.
2. Если sender внутри `vbiv_bot` ждёт ещё более богатый payload, enrichment может оказаться только частичным улучшением.
3. UI и отчёты теперь начнут видеть `partial_failure` вместо ложного `ok`.

## Проверка после исправления

Подтверждено:

1. Изменённые snapshot/mirror файлы компилируются без синтаксических ошибок.
2. upload path больше не помечает autofit seen после failed upload.
3. full cycle больше не теряет send-phase только из-за пустого pending queue.
4. retry path теперь получает vacancy context из локальной БД.

## Дополнительные улучшения

Следующий шаг для `Artem` уже operational:

1. перезапустить backend с этими правками;
2. снова нажать `Полный цикл`;
3. отдельно проверить, не остаётся ли внешний timeout к Google Sheets;
4. если timeout останется, уже идти в сетевой/Google API слой, а не снова в бизнес-логику.
