# 2026-06-01 incident patch hypothesis retry lead enrichment

## Анализ

Этот документ не внедряет код, а формулирует минимальный incident-specific patch hypothesis для симптома:

- `нет оффера для vacancy_id: ... ()`

после уже подтверждённых фактов:

1. matching `vacancy_id` в config существуют;
2. retry path передаёт `base_offer` в sender;
3. retry lead беднее обычного lead по schema.

## Причина

### 1. Наиболее вероятная incident-level первопричина

- Описание проблемы:
  - retry lead теряет часть контекста вакансии до входа в sender;
  - sender, вероятно, может увидеть `vacancy_id`, но не получить достаточно данных для полного offer resolution.
- Первопричина:
  - на границе `process_retry_queue -> run_sender -> run_campaign` retry lead несёт только урезанный payload.
- Критичность: `High`
- Возможные последствия:
  - terminal `SKIP` для лидов, у которых offer mapping фактически существует;
  - ложное впечатление, что причина в config, хотя это boundary/schema issue;
  - бесконечное повторение terminal items в retry queue.
- Рекомендуемое исправление:
  - обогатить retry lead теми полями, которые обычный send path уже использует.

### 2. Минимальный безопасный patch hypothesis

Самый осторожный кандидат сейчас:

1. не менять глобально sender contract;
2. не менять semantics `offer_mapping`;
3. перед `run_sender(retry_config, [retry_lead], ...)` восстановить для retry lead недостающие поля из локальной `leads` таблицы.

То есть вместо текущего минимального retry lead:

- `Фио`
- `Номер`
- `Город`
- `_source_type`
- `_raw_data.*`

стараться дополнить его до формы, ближе к обычному backlog lead:

- `Вакансия`
- `Дата`
- `Пол` при наличии
- возможно `Почта`, `Возраст`, `ДатаРождения` если доступны

### 3. Почему это выглядит безопаснее, чем менять sender вслепую

- Источник данных уже локальный и доменный:
  - `leads` таблица существует и сохраняет `vacancy`, `city`, `gender`, `lead_date`, `vacancy_id`, `response_id`, `resume_id`
- Изменение локализовано:
  - только retry reconstruction path
- Бизнес-логика offer mapping не меняется
- Риск случайно сломать обычный send path ниже, чем при правке неизвестного `vbiv_bot`

### 4. Что мешает идеальному patch прямо сейчас

Есть важное ограничение:

- текущий helper [get_latest_lead_meta_by_phones](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py) возвращает только:
  - `vacancy_id`
  - `response_id`
  - `resume_id`
  - `source_type`

Он не возвращает:

- `vacancy`
- `city`
- `gender`
- `lead_date`

Значит для patch path есть два варианта.

#### Вариант A. Наиболее реалистичный минимальный патч

Расширить существующий helper или добавить новый helper, который по телефону и owner возвращает последний lead record с:

- `vacancy`
- `city`
- `gender`
- `lead_date`
- `vacancy_id`
- `response_id`
- `resume_id`

И затем использовать эти поля для enrichment retry lead.

Плюсы:

- не требует менять queue schema;
- локализуется в доступных исходниках;
- хорошо согласуется с уже существующей `leads` таблицей.

Минусы:

- enrichment будет best-effort;
- если запись в `leads` уже недоступна или неоднозначна, lead останется урезанным.

#### Вариант B. Более правильный, но менее доступный сейчас

Сохранять vacancy title и другие нужные поля прямо в `retry_queue` в момент `add_to_retry_queue(...)`.

Плюсы:

- retry item самодостаточен;
- не нужен lookup обратно в `leads`.

Минусы:

- call sites `add_to_retry_queue(...)` в доступном source не видны;
- очень вероятно, что часть вызовов живёт в недостающем `modules.vbiv_bot`;
- значит безопасно внедрить этот вариант без полного source труднее.

### 5. Вероятности patch-гипотез

Оценка на текущем evidence:

1. `High probability ~0.75`
- минимальный fix должен быть именно в enrichment retry lead перед sender

2. `Medium probability ~0.20`
- нужен не только enrichment lead, но и адаптация sender к `_raw_data`/top-level field parsing

3. `Low probability ~0.05`
- root cause всё же в offer mapping layer, а не в retry schema gap

## План исправления

Если переходить от анализа к safe patch plan, порядок лучше такой:

1. Добавить helper для получения последнего lead context по телефону/owner.
2. В `process_retry_queue()` перед сборкой `retry_lead` попытаться подтянуть:
   - `Вакансия`
   - `Город`
   - `Пол`
   - `Дата`
3. Только если lookup ничего не дал, оставлять текущий degraded payload.
4. Не трогать пока sender internals, пока нет полного `vbiv_bot` source.

## Diff

Код не менялся.

Новый аналитический артефакт:

- [2026-06-01 incident patch hypothesis retry lead enrichment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20incident%20patch%20hypothesis%20retry%20lead%20enrichment.md)

Связанные документы:

- [2026-06-01 missing offer sender boundary analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20missing%20offer%20sender%20boundary%20analysis.md)
- [2026-06-01 lead payload schema gap analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20lead%20payload%20schema%20gap%20analysis.md)
- [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)

## Риски

Основные риски такого patch hypothesis:

1. Enrichment может подхватить не тот lead, если по телефону было несколько разных заявок.
2. Lookup по телефону без учёта дополнительных признаков может дать устаревший vacancy context.
3. Если sender на самом деле ждёт не только vacancy title, а совершенно другой raw structure, enrichment поможет не полностью.

Почему риск всё ещё управляемый:

- это best-effort improvement только для retry path;
- fallback на текущий behaviour можно сохранить;
- обычный send path не затрагивается.

## Проверка после исправления

После реального внедрения нужно будет проверить:

1. retry lead теперь содержит `Вакансия` и другие enrichment-поля;
2. problematic `vacancy_id` из incident больше не уходит в `нет оффера ... ()`;
3. обычная рассылка не меняет поведение;
4. terminal retry items по `missing offer` уменьшаются.

## Дополнительные улучшения

После такого минимального patch логично сделать следующее:

1. при появлении полного `vbiv_bot` source решить, нужен ли более строгий sender contract;
2. при необходимости перевести queue schema на self-contained retry records;
3. затем уже обновить `Wave 5` execution-pack из “queue lifecycle” в более полный “retry lifecycle + payload integrity”.
