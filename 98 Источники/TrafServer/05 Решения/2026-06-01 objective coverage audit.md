# 2026-06-01 objective coverage audit

## Анализ

Этот документ проверяет не новые баги, а степень покрытия исходной forensic-цели.

Цель на текущем этапе трактуется так:

1. разобрать структуру и стек проекта;
2. подтвердить текущее поведение по live server, логам и актуальным snapshot;
3. выделить root causes, а не только симптомы;
4. для каждой активной ветки зафиксировать:
   - критичность;
   - последствия;
   - безопасный путь исправления;
   - риски и post-fix проверки;
5. отделить active findings от historical findings;
6. довести результат до уровня implementation-ready roadmap.

Ниже используется шкала:

- `Covered` — подтверждено фактами и уже связано с patch/execution-материалами;
- `Partial` — есть сильная база, но остаются белые пятна или нет полного end-to-end доказательства;
- `Missing` — слой цели ещё не закрыт.

## Причина

### 1. Структура, стек, entry points, deploy-контур

- Статус: `Covered`
- Подтверждение:
  - [2026-06-01 consolidated root-cause report.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20root-cause%20report.md)
  - [2026-06-01 architecture map current server.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20architecture%20map%20current%20server.md)
  - [2026-06-01 operational map current deployment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20operational%20map%20current%20deployment.md)
- Что закрыто:
  - монорепо разложено на подсистемы;
  - entry points и основные конфиги перечислены;
  - контейнеры, домены, прокси и БД-контуры зафиксированы.

### 2. Revalidation текущего snapshot против старых выводов

- Статус: `Covered`
- Подтверждение:
  - [2026-06-01 revalidation current server snapshot.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20revalidation%20current%20server%20snapshot.md)
  - [2026-06-01 root cause matrix current state.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20root%20cause%20matrix%20current%20state.md)
- Что закрыто:
  - старые находки разведены на `active now` и `historical forensic`;
  - уже исправленные места не предлагаются как будто они всё ещё текущие.

### 3. Security-поверхность и operational access

- Статус: `Covered`
- Подтверждение:
  - [2026-06-01 wave 1 execution pack security hardening.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%201%20execution%20pack%20security%20hardening.md)
  - [2026-06-01 server-side ssh and proxy hardening plan.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20server-side%20ssh%20and%20proxy%20hardening%20plan.md)
  - [2026-06-01 redacted secret inventory.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20redacted%20secret%20inventory.md)
  - [2026-06-01 secret rotation priority plan.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20secret%20rotation%20priority%20plan.md)
- Что закрыто:
  - root password auth подтверждён;
  - secret sprawl подтверждён;
  - perimeter drift по AccountManager подтверждён;
  - есть execution-ready порядок hardening.

### 4. Runtime truthfulness по логам и run-level статусам

- Статус: `Covered`
- Подтверждение:
  - [2026-06-01 autolead 3 log analysis.md](C:/Users/Арт/Desktop/TrafServer/01%20Расследования/2026-06-01%20autolead%203%20log%20analysis.md)
  - [2026-06-01 run status and retry queue root causes.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20run%20status%20and%20retry%20queue%20root%20causes.md)
  - [2026-06-01 wave 4 execution pack run status truthfulness.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%204%20execution%20pack%20run%20status%20truthfulness.md)
- Что закрыто:
  - лог и код сведены вместе;
  - причина ложного `Ошибок: 0` подтверждена;
  - есть конкретный plan для phase-aware run status.

### 5. Retry lifecycle и terminal outcomes

- Статус: `Covered`
- Подтверждение:
  - [2026-06-01 run status and retry queue root causes.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20run%20status%20and%20retry%20queue%20root%20causes.md)
  - [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)
- Что закрыто:
  - queue-side дефект подтверждён по коду;
  - есть точка исправления жизненного цикла записи.

### 6. Config ownership drift и offer_mapping merge drift

- Статус: `Covered`
- Подтверждение:
  - [2026-06-01 config save cross-user drift confirmed.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20config%20save%20cross-user%20drift%20confirmed.md)
  - [2026-06-01 wave 2 execution pack config ownership split.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%202%20execution%20pack%20config%20ownership%20split.md)
  - [2026-06-01 offer mapping drift hypothesis confirmed by config merge.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20offer%20mapping%20drift%20hypothesis%20confirmed%20by%20config%20merge.md)
  - [2026-06-01 wave 3 execution pack offer mapping merge correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%203%20execution%20pack%20offer%20mapping%20merge%20correction.md)
- Что закрыто:
  - ownership-mixing подтверждён;
  - merge drift для `offer_mapping` подтверждён;
  - обе конфигурационные ветки доведены до implementation-плана.

### 7. Причинно-следственная карта и порядок внедрения

- Статус: `Covered`
- Подтверждение:
  - [2026-06-01 root cause matrix current state.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20root%20cause%20matrix%20current%20state.md)
  - [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
  - [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)
  - [2026-06-01 implementation index.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20index.md)
- Что закрыто:
  - findings сведены в wave-order;
  - есть validation gates;
  - execution-pack по активным волнам подготовлены.

### 8. Полнота live source по sender/downstream части

- Статус: `Partial`
- Подтверждение:
  - missing `modules.vbiv_bot` уже зафиксирован в offer/retry ветке расследования;
  - [2026-06-01 missing offer sender boundary analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20missing%20offer%20sender%20boundary%20analysis.md) уже подтверждает, что для инцидента из `autolead (3).log` matching `vacancy_id` есть в config, и фокус смещается на sender boundary;
  - [2026-06-01 lead payload schema gap analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20lead%20payload%20schema%20gap%20analysis.md) уже подтверждает, что normal send path и retry path несут разные lead schema;
  - queue-side симптомы подтверждены, но самый нижний sender source локально неполный.
- Что уже есть:
  - сильная гипотеза и несколько подтверждённых upstream-причин для `missing offer`;
  - narrowing evidence, что incident-specific проблема вероятнее на границе `process_retry_queue -> run_campaign`, а не просто в отсутствии маппинга;
  - подтверждённый schema gap между normal lead и retry lead;
  - execution-pack по ownership/merge/retry уже подготовлены.
- Что ещё не закрыто:
  - точное место формирования строки `нет оффера для vacancy_id` не доведено до полного live source.

### 9. Async/WS integration-proof уровня end-to-end

- Статус: `Partial`
- Подтверждение:
  - snapshot revalidation показал, что самая опасная часть уже смягчена;
  - интеграционная проверка доставки статусов всё ещё не выполнена end-to-end.
- Что уже есть:
  - architectural и code-level выводы;
  - понимание предыдущей причины.
- Что ещё не закрыто:
  - нет полного доказательства на живом потоке `job_start/job_done/job_error` от источника до UI.

### 10. DB/API schema-level exhaustiveness

- Статус: `Partial`
- Подтверждение:
  - [2026-06-01 db and api inventory current sources.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20db%20and%20api%20inventory%20current%20sources.md)
- Причина:
  - основные runtime/config/security дефекты доказаны без полного data-model inventory;
  - но исчерпывающая карта таблиц, миграций и API-контрактов не собрана.
- Вывод:
  - базовый inventory по трем data-plane и нескольким API-контурам уже собран;
  - но часть router/source покрытия всё ещё неполная, поэтому ветка остаётся `Partial`.

### 11. Performance / capacity / load behavior

- Статус: `Missing`
- Причина:
  - расследование шло как forensic/root-cause по correctness/security/ops;
  - нагрузочные характеристики, latency profile и capacity limits отдельно не исследовались.
- Вывод:
  - это не пробел в текущей root-cause ветке, но это отдельная незакрытая область.

## План исправления

Из coverage audit следует такой честный вывод:

1. Основная forensic-цель по `root cause + severity + consequences + safe patch path` уже `Covered`.
2. Не закрыты до конца только более глубокие интеграционные и exhaustiveness-слои:
   - полный sender source;
   - end-to-end WS delivery proof;
   - полный DB/API inventory;
   - performance/capacity branch.
3. Значит следующий шаг уже не новый общий отчёт, а осознанный выбор:
   - либо переходить к внедрению по execution-pack;
   - либо отдельно добирать один из `Partial/Missing` слоёв.

## Diff

Новый артефакт этого шага:

- [2026-06-01 objective coverage audit.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20objective%20coverage%20audit.md)

Рекомендуемые точки навигации после него:

- [2026-06-01 implementation index.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20index.md)
- [2026-06-01 consolidated root-cause report.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20root-cause%20report.md)

## Риски

Главный риск без такого audit:

- принять объём материалов за полноту доказательства;
- перепутать `implementation-ready` с `absolutely exhaustive`;
- начать утверждать то, что пока только `Partial`.

Самые важные оставшиеся ограничения:

- неполный live source по sender/downstream части;
- отсутствие полного WS end-to-end proof;
- отсутствие performance/capacity ветки.

## Проверка после исправления

Этот audit можно считать полезным, если он позволяет быстро ответить на три вопроса:

1. что уже закрыто на уровне доказательства;
2. что ещё остаётся частичным;
3. можно ли уже переходить к внедрению.

На текущем состоянии ответ такой:

- внедрение по активным execution-pack уже возможно;
- но это не означает, что exhaustiveness по всем слоям 100%.

## Дополнительные улучшения

Если продолжать именно forensic-ветку, следующие наиболее полезные варианты такие:

1. добрать live source sender-модуля и замкнуть `missing offer` до конца;
2. провести целевую end-to-end проверку WS status delivery;
3. собрать отдельный DB/API inventory;
4. открыть отдельную performance/capacity ветку, если это тоже нужно проекту.
