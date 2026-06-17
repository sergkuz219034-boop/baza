# Implementation roadmap by waves

Дата: 2026-06-01

Связанные документы:
- [2026-06-01 implementation index.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20index.md)
- [2026-06-01 root cause matrix current state.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20root%20cause%20matrix%20current%20state.md)
- [2026-06-01 patch-plan run status and retry queue.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20run%20status%20and%20retry%20queue.md)
- [2026-06-01 patch-plan offer mapping drift.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20offer%20mapping%20drift.md)
- [2026-06-01 patch-plan config save ownership split.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20config%20save%20ownership%20split.md)
- [2026-06-01 server-side ssh and proxy hardening plan.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20server-side%20ssh%20and%20proxy%20hardening%20plan.md)
- [2026-06-01 secret rotation priority plan.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20secret%20rotation%20priority%20plan.md)
- [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)
- [2026-06-01 wave 1 execution pack security hardening.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%201%20execution%20pack%20security%20hardening.md)
- [2026-06-01 wave 2 execution pack config ownership split.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%202%20execution%20pack%20config%20ownership%20split.md)
- [2026-06-01 wave 3 execution pack offer mapping merge correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%203%20execution%20pack%20offer%20mapping%20merge%20correction.md)
- [2026-06-01 wave 4 execution pack run status truthfulness.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%204%20execution%20pack%20run%20status%20truthfulness.md)
- [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)
- [2026-06-01 consolidated runtime patch bundle.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20runtime%20patch%20bundle.md)

## Анализ

Ниже дорожная карта не “по файлам”, а по волнам внедрения.

Цель:
- закрывать первопричины в таком порядке, чтобы не лечить downstream-симптомы раньше upstream-причин
- снижать риск lockout, config drift и ложных регрессий

## Волна 0. Подготовка

### Цель

Подготовить безопасную площадку перед изменениями.

### Закрывает

- риск operator error
- риск патчить уже исправленные места
- риск смешивать historical и active findings

### Действия

1. Работать только от текущего `remote_server_snapshot` и live state.
2. Не использовать старые diff-планы без сверки.
3. Подтвердить текущие backup/rollback точки:
- доступ по SSH
- резервный канал входа
- backup конфигов
- backup БД

### Проверки

- есть подтверждённый путь админского доступа
- понятен rollback по конфигам и compose
- нет намерения повторно применять already-fixed code patches

## Волна 1. Security hardening

### Цель

Сначала снизить наибольший blast radius.

### Закрывает

- RC-S1 root SSH password auth
- RC-S2 secret sprawl
- частично RC-S3 perimeter drift

### Основные действия

1. SSH:
- добавить рабочий key-based доступ
- проверить отдельную новую SSH-сессию
- затем отключить password auth

2. Secrets:
- не ротировать всё сразу
- начать с `Critical` auth/perimeter secrets
- подготовить separation по сервисам

3. Proxy drift:
- решить судьбу `ACCOUNT_MANAGER_BASIC_AUTH_*`
- либо включить в `Caddyfile`
- либо удалить мёртвую конфигурацию

### Затрагиваемые зоны

- server SSH config
- `.env`
- `docker-compose.yml`
- `deploy/Caddyfile`

### Основной риск

- lockout при преждевременном отключении password auth

### Обязательные проверки

- вход по ключу реально работает
- password auth больше не нужен
- домены отвечают после perimeter-изменений
- не потеряны критичные secrets при первой волне ротации

## Волна 2. Config ownership split

### Цель

Остановить генерацию нового config drift.

### Закрывает

- RC-C2 user save загрязняет shared config

### Основные действия

1. Разделить user save и shared save.
2. Убрать shared sync из обычных user-facing save flows по умолчанию.
3. Обновить тестовый контракт.

### Затрагиваемые файлы

- `remote_files/services/leads_service.py`
- `remote_files/tests/test_config_merge.py`
- user-facing routes, которые полагаются на `save_config(...)`

### Почему эта волна раньше merge-fix

Если сначала не остановить загрязнение shared base, то исправление merge semantics будет работать поверх продолжающегося drift.

### Основной риск

- вскроются скрытые зависимости на неявный shared sync

### Обязательные проверки

- user save больше не меняет shared HWID config
- local `config.json` и user profile продолжают сохраняться
- admin/migration путь shared save остаётся доступным

## Волна 3. Config merge correction

### Цель

Исправить уже существующий drift в `offer_mapping`.

### Закрывает

- RC-C1 user profile overlay может занулять shared `offer_mapping`

### Основные действия

1. Ввести явное правило для `offer_mapping`.
2. Не позволять пустому profile-offer-mapping безоговорочно затирать непустой shared mapping.
3. Добавить regression-тесты на existing-profile drift.

### Затрагиваемые файлы

- `remote_files/services/leads_service.py`
- `remote_files/tests/test_config_merge.py`

### Почему не раньше Волны 2

Потому что иначе новый drift всё равно будет продолжать записываться обратно через старую save-model.

### Основной риск

- изменение семантики “пустой список = отключить” против “пустой список = наследовать”

### Обязательные проверки

- пустой profile больше не убивает shared offers без явного решения
- непустой profile по-прежнему корректно переопределяет shared offers

## Волна 4. Runtime truthfulness

### Цель

Сделать статус цикла честным и диагностируемым.

### Закрывает

- RC-R1 run-level phase failure masking

### Основные действия

1. Расширить outcome `upload_sheets()`.
2. Передавать фазовый failure в `run_full_cycle()`.
3. Перестать всегда писать `status="ok"` в `run_log`.

### Затрагиваемые файлы

- `remote_server_snapshot/services/leads_service.py`
- возможно code paths в `api/routers/jobs.py`
- consumers `run_log.status`

### Основной риск

- UI и отчёты могут ожидать старую упрощённую модель статусов

### Обязательные проверки

- timeout Sheets больше не даёт `ok`
- нулевая нормальная выгрузка без ошибок остаётся `ok`
- run-log и UI не ломаются на новых статусах

## Волна 5. Retry lifecycle correction

### Цель

Развести terminal и retryable исходы, а также выровнять integrity retry payload.

### Закрывает

- RC-R2 terminal retry items
- RC-D2 retry semantics drift
- incident-class `missing offer` на границе retry payload -> sender resolver

### Основные действия

1. Добавить terminal classification для `missing_offer_mapping`.
2. Удалять или архивировать terminal retry items.
3. Не смешивать `skipped`, `terminal`, `duplicate`, `retryable_error`.
4. Best-effort обогащать retry lead vacancy context из локальной `leads` таблицы.

Рекомендуемое runtime-разбиение на коммиты уже сведено отдельно в:
- [2026-06-01 consolidated runtime patch bundle.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20runtime%20patch%20bundle.md)

### Затрагиваемые файлы

- `remote_server_snapshot/services/leads_service.py`
- `remote_server_snapshot/utils/database.py`
- downstream sender-module, если будет получен полный live source

### Почему после Волны 3

Часть `missing offer` симптомов может исчезнуть после исправления ownership/merge drift. Retry lifecycle лучше чинить уже после стабилизации offer resolution.

Но после пере-проверки инцидента из `autolead (3).log` подтверждено, что:
- для части `missing offer` mapping уже существует;
- значит в этой волне нужно чинить не только lifecycle, но и retry payload integrity.

### Основной риск

- неверно классифицировать временный сбой как terminal

### Обязательные проверки

- terminal missing-offer items перестают крутиться бесконечно
- временные ошибки продолжают корректно ретраиться
- retry lead больше не теряет vacancy context там, где он уже есть в локальной `leads` таблице

## Волна 6. Integration verification and cleanup

### Цель

Проверить спорные места и убрать устаревшие forensic допущения.

### Закрывает

- RC-R4 WS status delivery uncertainty
- RC-O1/RC-O2 диагностические process risks

### Основные действия

1. Интеграционно проверить WS-status delivery.
2. Обновить historical patch-plans, которые больше не актуальны.
3. Зафиксировать, какие старые root causes окончательно переведены в historical.

### Обязательные проверки

- UI получает job status end-to-end
- расследовательские документы больше не конфликтуют с текущим snapshot

## Порядок важен

Неправильный порядок даст ложные результаты:

- если чинить retry раньше config ownership, можно лечить шум, а не источник drift
- если чинить merge раньше ownership split, drift будет продолжать создаваться
- если чинить runtime truthfulness раньше security, останется критичный внешний риск

## Вывод

Рациональный порядок внедрения сейчас такой:

1. Security hardening
2. Config ownership split
3. Config merge correction
4. Run status truthfulness
5. Retry lifecycle correction
6. Integration verification and cleanup
