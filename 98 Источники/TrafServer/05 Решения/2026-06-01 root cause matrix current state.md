# Root cause matrix: current state

Дата: 2026-06-01

Связанные документы:
- [2026-06-01 consolidated root-cause report.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20root-cause%20report.md)
- [2026-06-01 revalidation current server snapshot.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20revalidation%20current%20server%20snapshot.md)
- [2026-06-01 run status and retry queue root causes.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20run%20status%20and%20retry%20queue%20root%20causes.md)
- [2026-06-01 offer mapping drift hypothesis confirmed by config merge.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20offer%20mapping%20drift%20hypothesis%20confirmed%20by%20config%20merge.md)
- [2026-06-01 config save cross-user drift confirmed.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20config%20save%20cross-user%20drift%20confirmed.md)
- [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
- [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)

## Анализ

Ниже матрица подтверждённых первопричин с разделением:

- что выглядит активным **сейчас**
- что является **исторической первопричиной**, но уже исправлено в текущем snapshot
- что является **связующей причиной**, усиливающей другие дефекты

## Матрица

### 1. Security / Access layer

#### RC-S1. Root SSH по паролю
- Статус: `Active now`
- Критичность: `Critical`
- Слой: infrastructure / access
- Симптомы:
  - высокий риск компрометации сервера
  - зависимость локальной операционки от password auth
- Подпитывает:
  - любой другой дефект становится опаснее из-за слабого периметра

#### RC-S2. Secret sprawl в общем `.env`
- Статус: `Active now`
- Критичность: `Critical`
- Слой: deployment / secrets
- Симптомы:
  - один env-file контролирует несколько security boundary
  - сложная ротация и большой blast radius
- Подпитывает:
  - auth drift
  - perimeter drift
  - операционные ошибки при ротации

#### RC-S3. Reverse proxy drift для Account Manager
- Статус: `Active now`
- Критичность: `Low/Medium`
- Слой: proxy / perimeter
- Симптомы:
  - compose/env говорят про basic auth, а Caddy не применяет его
- Подпитывает:
  - ложные operational assumptions

#### RC-S4. Дефолтный secret и fail-open auth в Account Manager
- Статус: `Historical, fixed in current snapshot`
- Критичность: `High`
- Слой: app auth
- Симптомы:
  - ранее создавали прямой риск auth bypass / token forgery
- Связь:
  - важны как forensic history, но не должны считаться активными без нового подтверждения

### 2. Runtime / observability layer

#### RC-R1. Run-level phase failure не поднимается в итоговый статус
- Статус: `Active in current snapshot until disproved`
- Критичность: `High`
- Слой: business runtime / observability
- Симптомы:
  - Sheets timeout даёт `Sheets: 0`, `Ошибок: 0`
  - `run_log` закрывается как `ok`
- Подпитывает:
  - ложный мониторинг
  - пропуск реальных operational сбоев

#### RC-R2. Terminal retry items не завершаются корректно
- Статус: `Active in current snapshot until disproved`
- Критичность: `Medium`
- Слой: queue lifecycle
- Симптомы:
  - записи с terminal `SKIP` могут крутиться повторно
- Подпитывает:
  - логовый шум
  - сложность диагностики

#### RC-R3. Graceful shutdown
- Статус: `Historical, fixed in current snapshot`
- Критичность: `High`
- Слой: lifecycle
- Симптомы:
  - раньше внешний restart выглядел как грязное падение
- Связь:
  - важен как часть forensic trail, но текущий snapshot уже содержит правки

#### RC-R4. WS delivery статусов задач
- Статус: `Mostly fixed / needs integration verification`
- Критичность: `Medium`
- Слой: UI observability
- Симптомы:
  - раньше job status мог теряться между thread и event loop
- Связь:
  - текущая самая опасная реализация уже ослаблена

### 3. Config / ownership layer

#### RC-C1. User profile overlay может занулять shared `offer_mapping`
- Статус: `Active in remote_files logic`
- Критичность: `High`
- Слой: config merge semantics
- Симптомы:
  - у части пользователей может исчезать offer mapping
  - downstream возникает `missing offer`
- Подпитывает:
  - retry queue noise
  - нестабильность рассылки

#### RC-C2. User save загрязняет shared config
- Статус: `Active in remote_files logic`
- Критичность: `High`
- Слой: config ownership
- Симптомы:
  - пользовательские изменения становятся shared HWID-базой
  - cross-user drift
- Подпитывает:
  - RC-C1
  - непредсказуемость runtime-поведения между профилями

#### RC-C3. Destructive import secrets
- Статус: `Historical, mitigated in current snapshot`
- Критичность: `Medium`
- Слой: settings import/export
- Симптомы:
  - раньше частичный import мог удалить лишние runtime secrets

### 4. Data / API layer

#### RC-D1. Owner binding в destructive settings endpoints
- Статус: `Historical, fixed in current snapshot`
- Критичность: `High`
- Слой: owner-scoped API / DB
- Симптомы:
  - раньше API мог возвращать `ok`, не очищая реальные данные пользователя

#### RC-D2. Retry queue semantics смешивает retryable и terminal outcomes
- Статус: `Active`
- Критичность: `Medium`
- Слой: queue/domain model
- Симптомы:
  - `skipped` и `terminal` не разведены
- Подпитывает:
  - RC-R2

### 5. Operational / deployment interpretation layer

#### RC-O1. Внешние container restarts ошибочно воспринимаются как app crashes
- Статус: `Active diagnostic risk`
- Критичность: `Medium`
- Слой: operations / interpretation
- Симптомы:
  - лог `Получен сигнал завершения` можно неверно читать как внутреннее падение
- Подпитывает:
  - неправильный приоритет исправлений
  - wasted debugging effort

#### RC-O2. Неполные локальные зеркала искажают выводы
- Статус: `Active process risk`
- Критичность: `Medium`
- Слой: forensic process
- Симптомы:
  - `remote_files` не содержит всех runtime-модулей
  - критичный sender-module отсутствует локально
- Подпитывает:
  - ложные или неполные root-cause explanations

## Причинно-следственные цепочки

### Цепочка A. `missing offer` / retry noise

1. RC-C2: user save загрязняет shared config
2. RC-C1: user profile overlay может занулять shared `offer_mapping`
3. downstream sender не находит корректный offer resolution
4. RC-D2 / RC-R2: terminal outcomes не отделены от retryable
5. в логах видно:
   - `нет оффера для vacancy_id`
   - бесконечный `SKIP` noise

### Цепочка B. “успешный” run при фактическом провале

1. Google Sheets phase падает по timeout
2. RC-R1: `upload_sheets()` схлопывает failure в `0`
3. `run_full_cycle()` закрывает `run_log` как `ok`
4. оператор видит `Ошибок: 0`

### Цепочка C. Ошибочная диагностика падений

1. RC-O1: внешний restart контейнера выглядит как “приложение упало”
2. исторический RC-R3 раньше действительно ухудшал shutdown
3. сейчас можно лечить уже исправленную проблему и пропустить реальную operational причину

## Приоритет по текущему состоянию

### Первая волна
- RC-S1 root SSH password auth
- RC-S2 secret sprawl
- RC-R1 run status masking
- RC-C2 config save ownership drift

### Вторая волна
- RC-C1 offer_mapping merge drift
- RC-R2 / RC-D2 terminal retry semantics
- RC-S3 reverse proxy drift

### Третья волна
- интеграционная проверка RC-R4 WS delivery
- cleanup historical notes / patch plans, уже закрытых в snapshot

## Вывод

На текущем этапе самая полезная картина такая:

- security-проблемы остаются самыми опасными;
- runtime-проблемы вокруг run/retry — самые заметные по симптомам;
- но их подпитывает более ранний конфигурационный дефект ownership/merge;
- часть старых code-level багов уже исправлена и должна рассматриваться как historical forensic context, а не как active defects by default.
