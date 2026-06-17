# Wave 5 execution pack: retry lifecycle correction

Дата: 2026-06-01

Связанные документы:
- [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
- [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)
- [2026-06-01 patch-plan run status and retry queue.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20run%20status%20and%20retry%20queue.md)
- [2026-06-01 run status and retry queue root causes.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20run%20status%20and%20retry%20queue%20root%20causes.md)
- [2026-06-01 offer mapping drift hypothesis confirmed by config merge.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20offer%20mapping%20drift%20hypothesis%20confirmed%20by%20config%20merge.md)
- [2026-06-01 missing offer sender boundary analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20missing%20offer%20sender%20boundary%20analysis.md)
- [2026-06-01 lead payload schema gap analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20lead%20payload%20schema%20gap%20analysis.md)
- [2026-06-01 incident patch hypothesis retry lead enrichment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20incident%20patch%20hypothesis%20retry%20lead%20enrichment.md)
- [2026-06-01 patch-plan retry lead enrichment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20retry%20lead%20enrichment.md)

## Анализ

Этот execution-pack теперь покрывает `Wave 5` в двух связанных подпроходах:

1. `retry lifecycle`
- отделить terminal retry outcomes от retryable
- прекратить бесконечный цикл `SKIP`-записей

2. `retry payload integrity`
- убрать schema gap между normal lead и retry lead
- не позволять incident-классу `missing offer` маскироваться как “нет маппинга”, когда mapping фактически существует

Подтверждённые факты по текущему snapshot:

- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:650)
  - `process_retry_queue(...)` повторно прогоняет due-items через `run_sender(...)`
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:690)
  - удаление из `retry_queue` происходит только для уже известных `send_history` элементов
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:735)
  - после `run_sender(...)` terminal outcome никак отдельно не обрабатывается
- [utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py:654)
  - `add_to_retry_queue(...)` увеличивает `retry_count` только в момент повторного добавления ошибки
- [utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py:704)
  - `get_due_retries()` выбирает все записи с `next_retry_at <= now` и `retry_count < max_retries`
- [utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py:718)
  - `remove_from_retry_queue(...)` умеет только удалять запись по `(phone, offer_name)`

Ключевой вывод:
- если due-item стабильно превращается в terminal `SKIP`
- и downstream не добавляет его обратно через `add_to_retry_queue(...)`
- то у него:
  - не растёт `retry_count`
  - не меняется `next_retry_at`
  - он снова попадает в `due_retries`

Это и есть подтверждённая механика бесконечного terminal noise.

Дополнительный подтверждённый вывод по incident-ветке:

- matching `vacancy_id` из `autolead (3).log` подтверждены в config;
- retry path формирует `base_offer`, но сам `retry_lead` остаётся беднее обычного lead;
- normal send path и retry path уже подтверждённо расходятся по schema;
- значит для `missing offer` есть не только queue-lifecycle причина, но и `payload integrity` причина.

## Причина

### 1. Модель очереди не различает terminal и retryable outcomes

Сейчас `process_retry_queue(...)` агрегирует только:
- `sent`
- `skipped`
- `errors`
- `duplicates`
- `retried`

Но не знает:
- terminal это outcome
- или временный

### 2. У очереди нет terminal completion path

Сейчас запись может завершиться естественно только если:
- она уже в `send_history`
- или downstream eventually дал `sent/duplicate`

Для terminal skip вроде `missing_offer_mapping` этого пути нет.

### 3. `retry_count` в текущей модели не является счётчиком фактических обработок due-item

Он растёт только в `add_to_retry_queue(...)`, а не после каждого due-processing pass.

Значит:
- очередь не умеет “выдыхаться” сама по себе для terminal items

### 4. Retry path несёт урезанный lead payload

Для обычного backlog lead уже подтверждены поля:
- `Вакансия`
- `Город`
- `Пол`
- `Дата`
- `_raw_data.vacancy_id`

Для retry lead подтверждены только:
- `Фио`
- `Номер`
- `Город`
- `_source_type`
- `_raw_data.vacancy_id`

Вывод:
- даже при существующем offer mapping sender может не получить достаточно vacancy context;
- это делает `payload integrity` частью `Wave 5`, а не отдельным unrelated incident.

## План исправления

### Шаг 1. Ввести terminal classification

Минимально нужен классификатор вроде:

```python
_classify_terminal_retry_outcome(retry_stats: dict, item: dict) -> str | None
```

Рекомендуемый первый terminal reason:
- `missing_offer_mapping`

### Шаг 2. Добавить explicit terminal completion path

При terminal outcome:
- либо удалять запись из `retry_queue`
- либо переносить её в отдельный audit/terminal store

Переходно и безопасно:
- удалять из `retry_queue`
- логировать terminal reason отдельно

### Шаг 3. Не смешивать terminal с обычным `skipped`

Минимально:
- terminal не должен жить как “просто skipped”
- `process_retry_queue()` должен различать:
  - `terminal`
  - `duplicate`
  - `retryable_error`
  - `skip` по безобидным причинам

### Шаг 4. Добавить retry lead enrichment

Минимальный безопасный путь:

- не трогать пока `run_sender()` и недоступный `modules.vbiv_bot`
- перед `run_sender(...)` best-effort обогащать retry lead из локальной `leads` таблицы

Нужно вернуть хотя бы:
- `Вакансия`
- `Город`
- `Пол`
- `Дата`

Это снижает вероятность того, что retry path сломается на resolver boundary при уже существующем `vacancy_id`.

## Diff

### 1. Новый классификатор

```diff
# remote_server_snapshot/services/leads_service.py
+ def _classify_terminal_retry_outcome(retry_stats: dict, item: dict) -> str | None:
+     # Переходная реализация: опираемся на downstream reason/lead_results, если они появятся
+     ...
```

Пока прямой machine-readable reason не подтверждён из sender-module, переходный путь:
- расширить downstream `run_campaign(...)`/`lead_results`
- возвращать reason для terminal outcomes

### 2. Новая ветка в `process_retry_queue()`

```diff
        terminal_reason = _classify_terminal_retry_outcome(retry_stats, item)
        if terminal_reason:
            remove_from_retry_queue(phone, offer_name)
            logger.info(
                "process_retry_queue: terminal retry removed %s (%s)",
                history_key,
                terminal_reason,
            )
            continue
```

### 3. Переходный вариант без отдельной таблицы

На первом шаге не требуется миграция БД.

Можно оставить:
- только удаление terminal items
- плюс отдельный лог

Позже улучшить до:
- `terminal_retry_audit`
- или history-table

### 4. Patch path для payload integrity

```diff
# remote_server_snapshot/utils/database.py
+ def get_latest_lead_context_by_phones(...):
+     ...
```

```diff
# remote_server_snapshot/services/leads_service.py
+ lead_context_by_phone = get_latest_lead_context_by_phones(...)
+
+ retry_lead = {
+     "Фио": ...,
+     "Номер": ...,
+     "Вакансия": vacancy_name,
+     "Город": city,
+     "Пол": gender,
+     "Дата": lead_date,
+     "_source_type": source_type,
+     "_raw_data": {...},
+ }
```

Подробный ready-to-apply план уже вынесен в:
- [2026-06-01 patch-plan retry lead enrichment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20retry%20lead%20enrichment.md)

## Почему это безопасно

1. Очередь перестаёт бесконечно крутить заведомо безнадёжные записи.
2. Изменение локализовано:
- `process_retry_queue(...)`
- возможно downstream sender return contract
3. Не требует немедленного изменения схемы БД, если стартовать с простого удаления + логирования.
4. Для payload integrity safest path тоже локализован:
- helper в `utils/database.py`
- enrichment в `process_retry_queue(...)`
- обычная send path не меняется

## Побочные эффекты

### Ожидаемые

- размер `retry_queue` уменьшится
- логовый шум от terminal `missing offer` снизится
- часть retry items начнёт успешно доходить до resolver logic, если проблема была именно в бедном payload

### Возможные скрытые

- если временная ошибка будет ошибочно признана terminal, запись исчезнет слишком рано
- это главный риск этой волны
- enrichment lookup по телефону может подтянуть устаревший vacancy context

## Проверка после исправления

### Обязательные проверки

1. Terminal missing-offer item:
- не возвращается в каждом цикле
- больше не висит в `due_retries`

2. Retryable error:
- продолжает жить в очереди
- повторно обрабатывается позже

3. `get_retry_queue_size()`:
- уменьшается после вымывания terminal items

4. Логи:
- содержат явный terminal reason
- не смешивают terminal outcome с обычным `skipped`

5. Retry lead перед `run_sender()`:
- содержит `Вакансия`
- содержит `Дата`
- содержит `_raw_data.vacancy_id`

6. Incident-класс `нет оффера для vacancy_id: ... ()`:
- больше не воспроизводится для записей, где mapping уже существует

## Открытый вопрос

Сейчас всё ещё не хватает полного live source для downstream sender-module, чтобы:

1. доказать лучший machine-readable signal из `lead_results`
2. точно подтвердить, какие поля lead обязательны для offer resolution

Поэтому безопасная промежуточная стратегия такая:

1. не угадывать terminal reason из текста лога
2. сначала закрыть queue-side problem
3. параллельно закрыть retry payload integrity через локальный enrichment
4. sender internals трогать только после появления полного `vbiv_bot` source
