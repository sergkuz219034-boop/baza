# 2026-06-01 missing offer sender boundary analysis

## Анализ

Этот документ уточняет sender-ветку для симптома из [autolead (3).log](C:/Users/Арт/Downloads/autolead%20(3).log):

- `[SKIP] ... нет оффера для vacancy_id: 54244364 ()`
- `[SKIP] ... нет оффера для vacancy_id: 54267737 ()`
- `[SKIP] ... нет оффера для vacancy_id: 54279842 ()`
- `[SKIP] ... нет оффера для vacancy_id: 54279727 ()`

Цель этого шага — понять, это проблема отсутствующего маппинга в конфиге или проблема на границе `process_retry_queue -> run_campaign`.

## Причина

### 1. Для проблемных `vacancy_id` маппинг в конфиге у `artem` реально существует

- Статус: `confirmed`
- Источник:
  - `control.db -> user_app_configs(login='artem')`
  - `control.db -> app_configs(hwid='9f03a58b9fd366da')`

Подтверждено:

- и user-scoped config `artem`,
- и shared HWID-config

содержат оффер `Воксис`, в который уже входят:

- `54244364`
- `54267737`
- `54279842`
- `54279727`

Вывод:

- для этого конкретного лога гипотеза “в конфиге вообще нет соответствующего оффера” не подтверждается;
- для этих четырёх ID она выглядит слабой.

### 2. Job run идёт в user-bound context, а не в безымянном глобальном режиме

- Статус: `confirmed for dashboard-triggered run path`
- Источник:
  - [jobs.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/routers/jobs.py)

Подтверждено:

- `run_job()` передаёт `_.username` в `_run_in_thread(...)`
- `_run_in_thread(...)` оборачивает `leads_service.load_config()` и дальнейший run в `bind_current_username(username)`

Вывод:

- для запуска из dashboard путь загрузки конфига user-scoped;
- это ещё сильнее ослабляет гипотезу, что sender использовал “не тот” конфиг из-за отсутствия user context.

Ограничение:

- это не доказывает, что анализируемый запуск был именно dashboard-triggered, но такой путь подтверждён и согласуется с owner-scoped логикой вокруг retry queue.

### 3. `process_retry_queue()` уже формирует для retry попытки оффер с нужным `vacancy_id`

- Статус: `confirmed`
- Источник:
  - [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py)

Подтверждено:

1. `offers_by_name` строится из `config["offer_mapping"]`
2. если `offer_name` найден, берётся существующий `base_offer`
3. если не найден, создаётся fallback-offer
4. если у fallback-offer нет `vacancy_ids`, туда принудительно добавляется `item["vacancy_id"]`
5. в `retry_config["offer_mapping"]` передаётся ровно `[base_offer]`

Вывод:

- на вход `run_sender()` retry path уже не должен приходить совсем без offer candidate;
- даже degraded path всё равно несёт `vacancy_id` в `base_offer`.

### 4. Самая сильная активная гипотеза теперь находится на sender boundary

- Статус: `strong hypothesis`
- Причина:
  - upstream config matching уже подтверждён;
  - retry-side reconstruction оффера тоже подтверждена;
  - но downstream source `modules.vbiv_bot` локально отсутствует.

Наиболее вероятные гипотезы сейчас:

1. `High probability ~0.70`
- `modules.vbiv_bot.run_campaign()` ожидает другой формат lead payload, чем тот, который собирает `process_retry_queue()`
- особенно подозрительно:
  - retry lead содержит `vacancy_id` только внутри `_raw_data`
  - не содержит явного top-level `vacancy_id`
  - не содержит названия вакансии
- лог `нет оффера для vacancy_id: ... ()` хорошо согласуется с тем, что vacancy ID уже виден, а vacancy title/offer resolution ломается на boundary parsing

2. `Medium probability ~0.20`
- внутри sender есть type/field mismatch при сравнении `vacancy_id` с `offer_mapping[*].vacancy_ids`
- например:
  - `str` vs `int`
  - поиск не в `vacancy_ids`, а в другом поле
  - чтение не из `_raw_data`, а из иного ключа

3. `Low probability ~0.10`
- для анализируемого run всё же использовался не тот config context
- эта версия стала слабее из-за:
  - наличия matching IDs в user config
  - наличия matching IDs в shared config
  - dashboard path с `bind_current_username`

### 5. Уже найденный `offer_mapping drift` остаётся системной причиной, но не выглядит главным объяснением именно этого лога

- Статус: `still valid system-level cause, weaker for this incident`

Важно разделять:

1. системный риск:
- merge/save drift по `offer_mapping` реален и уже подтверждён ранее

2. конкретный incident в [autolead (3).log](C:/Users/Арт/Downloads/autolead%20(3).log):
- здесь matching IDs в текущем control-store уже есть
- значит именно для этого кейса более вероятен sender-boundary дефект, а не отсутствие оффера в конфиге

## План исправления

Для forensic-ветки следующий лучший порядок такой:

1. Не считать больше “missing offer” в этом логе простым отсутствием конфигурации.
2. Зафиксировать, что активный фокус сместился на `modules.vbiv_bot`.
3. При первой возможности добыть live source или релевантный фрагмент `modules.vbiv_bot` и проверить:
   - откуда именно читается `vacancy_id`
   - как нормализуются типы
   - какие поля lead payload считаются обязательными для offer resolution
4. После этого уже решать:
   - это retry-only boundary bug
   - или общий resolver bug и для обычной send path тоже.

## Diff

Новый артефакт:

- [2026-06-01 missing offer sender boundary analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20missing%20offer%20sender%20boundary%20analysis.md)

Связанные документы:

- [2026-06-01 autolead 3 log analysis.md](C:/Users/Арт/Desktop/TrafServer/01%20Расследования/2026-06-01%20autolead%203%20log%20analysis.md)
- [2026-06-01 offer mapping drift hypothesis confirmed by config merge.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20offer%20mapping%20drift%20hypothesis%20confirmed%20by%20config%20merge.md)
- [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)

## Риски

Главный риск неправильной интерпретации сейчас такой:

- продолжать лечить `missing offer` только через config/offer_mapping layer,
- хотя для этого incident наиболее вероятен дефект на sender boundary.

Второй риск:

- перепутать системную причину и incident-specific причину.

То есть:

- `offer_mapping drift` всё ещё реален как root cause класса проблем,
- но именно для этого лога он уже не выглядит ведущим объяснением.

## Проверка после исправления

Этот шаг можно считать полезным, если он изменяет качество гипотез так:

1. раньше:
- “скорее всего нет маппинга”

2. теперь:
- “маппинг для этих ID подтверждён, значит искать надо на sender boundary”

На текущем состоянии это условие выполнено.

## Дополнительные улучшения

Следующий самый ценный шаг по sender-ветке:

1. достать live source `modules.vbiv_bot`;
2. либо, если source недоступен, получить его stack fragments / debug logs / printouts по resolver path;
3. затем проверить, одинаково ли обрабатываются:
   - обычный lead из pending/backlog
   - retry lead из `process_retry_queue()`.
