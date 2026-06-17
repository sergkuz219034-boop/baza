# Implementation index

Дата: 2026-06-01

## Анализ

Этот файл — короткий навигатор по пакету расследования и внедрения.

Используй его как стартовую точку, если нужно быстро понять:
- что уже подтверждено;
- что активное, а что historical;
- в каком порядке читать документы;
- к какому execution-pack переходить дальше.

## Причина

К этому моменту расследование разрослось на несколько слоёв:

1. forensic-отчёты
2. root-cause матрица
3. roadmap по волнам
4. validation checklist
5. execution-pack по отдельным волнам

Без index по ним уже неудобно ориентироваться.

## План исправления

### Если нужен общий обзор

Начать с:

- [2026-06-01 consolidated root-cause report.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20root-cause%20report.md)
- [2026-06-01 objective coverage audit.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20objective%20coverage%20audit.md)
- [2026-06-01 db and api inventory current sources.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20db%20and%20api%20inventory%20current%20sources.md)
- [2026-06-01 revalidation current server snapshot.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20revalidation%20current%20server%20snapshot.md)
- [2026-06-01 root cause matrix current state.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20root%20cause%20matrix%20current%20state.md)

### Если нужен порядок внедрения

Читать:

- [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
- [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)

### Если нужен security-first путь

Читать:

- [2026-06-01 wave 1 execution pack security hardening.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%201%20execution%20pack%20security%20hardening.md)

Дополнительно:

- [2026-06-01 server-side ssh and proxy hardening plan.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20server-side%20ssh%20and%20proxy%20hardening%20plan.md)
- [2026-06-01 secret rotation priority plan.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20secret%20rotation%20priority%20plan.md)

### Если нужен config-first путь

Читать по порядку:

1. [2026-06-01 wave 2 execution pack config ownership split.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%202%20execution%20pack%20config%20ownership%20split.md)
2. [2026-06-01 wave 3 execution pack offer mapping merge correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%203%20execution%20pack%20offer%20mapping%20merge%20correction.md)

### Если нужен runtime-first путь

Читать по порядку:

1. [2026-06-01 consolidated runtime patch bundle.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20runtime%20patch%20bundle.md)
2. [2026-06-01 wave 4 execution pack run status truthfulness.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%204%20execution%20pack%20run%20status%20truthfulness.md)
3. [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)

Если нужен incident-level разбор `missing offer`:

- [2026-06-02 Artem full cycle upload and send root cause.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-02%20Artem%20full%20cycle%20upload%20and%20send%20root%20cause.md)
- [2026-06-01 missing offer sender boundary analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20missing%20offer%20sender%20boundary%20analysis.md)
- [2026-06-01 lead payload schema gap analysis.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20lead%20payload%20schema%20gap%20analysis.md)
- [2026-06-01 incident patch hypothesis retry lead enrichment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20incident%20patch%20hypothesis%20retry%20lead%20enrichment.md)
- [2026-06-01 patch-plan retry lead enrichment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20retry%20lead%20enrichment.md)

## Diff

Реально подготовленные execution-pack:

- Wave 1: [2026-06-01 wave 1 execution pack security hardening.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%201%20execution%20pack%20security%20hardening.md)
- Wave 2: [2026-06-01 wave 2 execution pack config ownership split.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%202%20execution%20pack%20config%20ownership%20split.md)
- Wave 3: [2026-06-01 wave 3 execution pack offer mapping merge correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%203%20execution%20pack%20offer%20mapping%20merge%20correction.md)
- Wave 4: [2026-06-01 wave 4 execution pack run status truthfulness.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%204%20execution%20pack%20run%20status%20truthfulness.md)
- Wave 5: [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)

Отдельный bundle для runtime-внедрения:

- [2026-06-01 consolidated runtime patch bundle.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20runtime%20patch%20bundle.md)

## Риски

Главный навигационный риск:

- читать старые patch-plans без revalidation current snapshot;
- переходить к Wave 4/5 раньше Wave 2/3, если цель — лечить первопричину `missing offer`;
- начинать runtime/config волну, оставив открытым `Critical` security-risk без осознанного решения.

## Проверка после исправления

Этот index считается полезным, если позволяет быстро выбрать один из сценариев:

1. `security-first`
2. `config-first`
3. `runtime-first`
4. `full-wave order`

И не требует перечитывать весь пакет расследования ради выбора следующего шага.

## Дополнительные улучшения

Следующий шаг уже не в документации, а в исполнении:

- либо выбрать одну волну и начать реальное внедрение,
- либо на этом этапе использовать execution-pack как основу для ревью/утверждения порядка изменений. 
