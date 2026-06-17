# Consolidated runtime patch bundle

Дата: 2026-06-01

Связанные документы:
- [2026-06-01 implementation index.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20index.md)
- [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
- [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)
- [2026-06-01 wave 4 execution pack run status truthfulness.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%204%20execution%20pack%20run%20status%20truthfulness.md)
- [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)
- [2026-06-01 patch-plan retry lead enrichment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20retry%20lead%20enrichment.md)

## Анализ

Этот bundle связывает runtime-ветку в один внедряемый пакет:

1. `Wave 4`
- честный `run_status`
- фазовая truthfulness для Sheets/upload

2. `Wave 5A`
- terminal vs retryable lifecycle
- прекращение бесконечного terminal noise в `retry_queue`

3. `Wave 5B`
- retry payload integrity
- enrichment retry lead перед sender boundary

Ключевой вывод:
- `Wave 4` и `Wave 5` логически связаны, но не обязаны идти одним коммитом;
- лучший operational путь сейчас — один runtime bundle, но 3 маленьких коммита.

Почему это важно:
- `Wave 4` меняет observability и статусную правду;
- `Wave 5A` меняет lifecycle очереди;
- `Wave 5B` меняет содержимое retry payload.

Это три разных класса риска, и их лучше уметь откатывать по отдельности.

## Причина

### 1. `Wave 4` стоит первой внутри runtime bundle

Пока `run_status` врёт, следующие изменения труднее оценивать:
- retry мог реально улучшиться, но run всё ещё будет выглядеть `ok` при сбое Sheets;
- или наоборот, мы не увидим, что новая логика дала `partial_failure`.

Значит сначала нужно сделать систему наблюдаемой.

### 2. `Wave 5A` лучше отделить от `Wave 5B`

`Wave 5A` отвечает на вопрос:
- умеет ли очередь завершать terminal items

`Wave 5B` отвечает на другой вопрос:
- получает ли retry path достаточно данных, чтобы вообще не превращаться в terminal `missing offer`

Если смешать их в один коммит:
- будет труднее понять, что именно уменьшило шум;
- rollback тоже станет грубее.

### 3. `Wave 5B` не должна ждать полного sender-source

Для incident-класса `нет оффера для vacancy_id: ... ()` уже подтверждено:
- mapping существует;
- retry payload беднее normal lead;
- safest локальная правка — enrichment из `leads` table до входа в sender.

Это уже достаточно сильное основание для локального patch path, даже без полного `modules.vbiv_bot`.

## План исправления

Рекомендуемое разбиение на коммиты:

### Коммит 1. `Wave 4`

Содержимое:
- richer result у `upload_sheets()`
- phase failure tracking в `run_full_cycle()`
- вычисляемый `run_status`
- адаптация upload path в `api/routers/jobs.py`

Почему отдельно:
- это чистая observability/runtime truthfulness правка;
- её можно проверить без влияния на retry payload.

### Коммит 2. `Wave 5A`

Содержимое:
- terminal classification
- terminal completion path
- явное различение:
  - `terminal`
  - `retryable_error`
  - `duplicate`
  - `skipped`

Почему отдельно:
- это меняет lifecycle очереди;
- позволяет увидеть, уменьшается ли `retry_queue` даже без enrichment.

### Коммит 3. `Wave 5B`

Содержимое:
- helper вида `get_latest_lead_context_by_phones(...)`
- best-effort enrichment retry lead из `leads`
- добавление полей:
  - `Вакансия`
  - `Город`
  - `Пол`
  - `Дата`

Почему отдельно:
- это incident-oriented patch;
- его проще откатить отдельно, если enrichment окажется слишком агрессивным.

## Diff

Bundle не предлагает новый “четвёртый” patch-plan. Он собирает уже подготовленные:

1. `Wave 4`:
- [2026-06-01 wave 4 execution pack run status truthfulness.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%204%20execution%20pack%20run%20status%20truthfulness.md)

2. `Wave 5A/5B`:
- [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)
- [2026-06-01 patch-plan retry lead enrichment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20retry%20lead%20enrichment.md)

Практическое разбиение по файлам:

### Коммит 1
- `remote_server_snapshot/services/leads_service.py`
- `remote_server_snapshot/api/routers/jobs.py`

### Коммит 2
- `remote_server_snapshot/services/leads_service.py`
- при необходимости небольшой database helper/update path для terminal handling

### Коммит 3
- `remote_server_snapshot/utils/database.py`
- `remote_server_snapshot/services/leads_service.py`

## Риски

Главные риски bundle:

1. Если объединить `Wave 4` и `Wave 5A` в один коммит:
- станет сложнее отличить regressions observability от regressions queue lifecycle.

2. Если объединить `Wave 5A` и `Wave 5B` в один коммит:
- снижение `retry_queue` и исчезновение `missing offer` будет трудно причинно объяснить.

3. Если делать `Wave 5B` раньше `Wave 5A`:
- enrichment может помочь incident-ветке,
- но terminal items всё равно останутся крутиться бесконечно.

4. Если делать `Wave 5A` без осторожной классификации:
- можно удалить временные ошибки как terminal.

## Проверка после исправления

### После Коммита 1

Проверить:
- timeout Sheets больше не закрывает run как `ok`
- обычный zero-add upload без ошибки остаётся `ok`
- `run_statistics()` и consumers `run_log.status` живы

### После Коммита 2

Проверить:
- terminal `missing_offer_mapping` больше не возвращается в каждом цикле
- временные retryable ошибки не удаляются преждевременно
- размер `retry_queue` реально начинает уменьшаться

### После Коммита 3

Проверить:
- retry lead содержит vacancy context
- `нет оффера для vacancy_id: ... ()` у already-mapped `vacancy_id` исчезает или резко сокращается
- enrichment не подставляет массово нерелевантные вакансии

### Bundle-level критерий успеха

Runtime bundle считается успешным, если одновременно выполнены три условия:

1. run-level truthfulness больше не врёт про Sheets timeout;
2. terminal retry items больше не крутятся бесконечно;
3. retry path больше не теряет vacancy context там, где он уже есть в `leads`.

## Дополнительные улучшения

После runtime bundle следующим наиболее полезным шагом будет один из двух:

1. Реально внедрять `Wave 2` и `Wave 3`, если цель — убрать upstream причины `missing offer`.
2. Добрать live sender-source `modules.vbiv_bot`, чтобы:
- уточнить machine-readable terminal reasons;
- подтвердить, какие поля обязательны для offer resolution;
- решить, нужен ли после enrichment ещё один sender-side patch.
