# 2026-06-01 lead payload schema gap analysis

## Анализ

Этот документ уточняет sender-boundary проблему через сравнение двух подтверждённых payload shape:

1. обычный lead для send/backlog path
2. retry lead из `process_retry_queue()`

Цель: понять, есть ли уже на уровне доступного кода сильный сигнал schema mismatch, даже без полного source `modules.vbiv_bot`.

## Причина

### 1. Обычный backlog lead содержит заметно более богатый payload

- Статус: `confirmed`
- Источник:
  - [utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py)

`load_leads_for_send()` формирует lead такого вида:

- `Номер`
- `Фио`
- `Вакансия`
- `Город`
- `Пол`
- `Дата`
- `Почта`
- `Возраст`
- `ДатаРождения`
- `_source_type`
- `_raw_data.vacancy_id`
- `_raw_data.response_id`
- `_raw_data.resume_id`

Вывод:

- обычный send/backlog path несёт не только ID вакансии, но и её человекочитаемое название;
- в lead есть больше полей для fallback-resolution и логирования.

### 2. Retry lead существенно беднее

- Статус: `confirmed`
- Источник:
  - [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py)

`process_retry_queue()` формирует retry lead такого вида:

- `Фио`
- `Номер`
- `Город`
- `_source_type`
- `_raw_data.vacancy_id`
- `_raw_data.response_id`
- `_raw_data.resume_id`

Чего в retry lead нет:

- `Вакансия`
- `Пол`
- `Дата`
- `Почта`
- `Возраст`
- `ДатаРождения`
- top-level `vacancy_id`

Вывод:

- retry path передаёт sender-у более узкий schema contract;
- если `run_campaign()` или его helper ожидают top-level поля или vacancy title, retry lead объективно менее совместим.

### 3. Лог `нет оффера для vacancy_id: ... ()` хорошо согласуется с отсутствием vacancy title

- Статус: `strong correlation`
- Источник:
  - [autolead (3).log](C:/Users/Арт/Downloads/autolead%20(3).log)

Форма сообщения:

- `нет оффера для vacancy_id: 54244364 ()`

Сигнал:

- `vacancy_id` уже известен;
- скобки пустые, что очень похоже на отсутствие vacancy title/name в переданном payload.

Это не абсолютное доказательство, но это хорошо совпадает с тем, что retry lead:

- сохраняет `vacancy_id` в `_raw_data`;
- не несёт поля `Вакансия`.

### 4. Schema mismatch теперь выглядит самой сильной incident-level гипотезой

- Статус: `highest-probability incident cause`

Оценка гипотез после сравнения payload:

1. `High probability ~0.80`
- retry lead не удовлетворяет ожидаемому sender contract по полям вакансии;
- особенно вероятно ожидание:
  - top-level vacancy field
  - vacancy title/name
  - более полного raw structure

2. `Medium probability ~0.15`
- sender читает `vacancy_id` из другого места или ждёт другой тип

3. `Low probability ~0.05`
- проблема всё же в отсутствии offer mapping для этого инцидента

Последняя версия стала ещё слабее, потому что:

- matching IDs в config подтверждены;
- retry path передаёт `base_offer` с нужным `vacancy_id`;
- shape mismatch уже виден прямо в доступном коде.

### 5. Source gap остаётся, но уже не мешает выделить ведущую первопричину incident-класса

- Статус: `partial proof with strong narrowing`

Мы всё ещё не видим:

- `modules.vbiv_bot.run_campaign`
- `utils.data_processor.normalize_lead`
- `modules.rabota_api.RabotaRuClient`

Но даже без них уже подтверждено:

- normal send path и retry path не эквивалентны по схеме lead payload;
- incident из `autolead (3).log` лучше всего объясняется именно этим разрывом.

## План исправления

Следующий forensic-шаг теперь ещё точнее:

1. Добыть `modules.vbiv_bot` и проверить, какие поля lead обязательны для offer resolution.
2. Если source недоступен, получить debug traces именно по:
   - входному lead dict
   - extracted vacancy_id
   - extracted vacancy title/name
   - matched offer candidate
3. Отдельно сравнить:
   - обычный pending/backlog lead
   - retry lead
   на момент входа в sender.

## Diff

Новый артефакт:

- [2026-06-01 lead payload schema gap analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20lead%20payload%20schema%20gap%20analysis.md)

Связанные документы:

- [2026-06-01 missing offer sender boundary analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20missing%20offer%20sender%20boundary%20analysis.md)
- [2026-06-01 autolead 3 log analysis.md](C:/Users/Арт/Desktop/TrafServer/01%20Расследования/2026-06-01%20autolead%203%20log%20analysis.md)

## Риски

Главный риск сейчас:

- пытаться чинить только очередь retry или только `offer_mapping`,
- не признавая, что normal и retry lead shape уже расходятся на границе sender-а.

Второй риск:

- переоценить силу доказательства без live source.

Честная граница утверждения такая:

- schema gap подтверждён;
- что именно внутри `vbiv_bot` ломается на этом gap, ещё не доказано окончательно.

## Проверка после исправления

Этот шаг можно считать полезным, если он отвечает на вопрос:

- есть ли уже в доступном коде объективная разница между normal lead и retry lead?

Ответ сейчас: да.

И эта разница:

- достаточно сильна,
- хорошо совпадает с формой лога,
- и делает schema mismatch главным кандидатом на incident-level root cause.

## Дополнительные улучшения

Следующий лучший шаг по этой ветке:

1. получить live source `vbiv_bot`;
2. либо получить сырой debug dump входного lead перед resolver logic;
3. после этого уже можно будет перевести sender/downstream ветку из `Partial` в почти `Covered`.
