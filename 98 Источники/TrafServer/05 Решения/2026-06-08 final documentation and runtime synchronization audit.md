# Final documentation and runtime synchronization audit

Теги: #решение #аудит

## Контекст

К 8 июня 2026 задача состояла уже не только в локальных фикcах, а в синхронизации:

- live server runtime;
- container topology;
- runtime/storage layout;
- access checks;
- README;
- docs/*;
- Obsidian wiki;
- operational helper scripts.

Источником истины считались:

- live server `/root/TrafficHub`
- синхронизированный `remote_server_snapshot/docker-compose.yml`
- текущий код в workspace

## Что точно синхронизировано

### Live runtime и контейнеры

- worker выделен как отдельный контейнер;
- у worker есть heartbeat-healthcheck;
- `license_auth` не использует общий `data`;
- `account_manager` не использует общий `secrets`;
- удалена лишняя `account_manager_net`;
- основная схема сети теперь `core_net + edge_net`.

### Storage / secrets layout

- runtime SQLite/state вынесены в `data/runtime/`;
- runtime secrets вынесены в `data/runtime/secrets/`;
- системные ключи и identity-файлы оставлены в `secrets/`;
- совместимость со старыми относительными путями сохранена на уровне кода;
- runtime config уже мигрирован на новый container-runtime путь service account: `/app/data/runtime/secrets/service_account.json`;
- код нормализации дополнительно умеет переживать старые host-path значения и приводить их к container-path при runtime access checks.

### Access / owner scope

- пустой экран “Сначала загрузите secrets / импортируйте настройки” для всех пользователей устранён;
- `AutoleadAccess` больше не ломается из-за старого `service_account_file` path;
- `AutoleadAccess` и startup checks больше не ломаются из-за host-path значений вида `/root/TrafficHub/data/runtime/secrets/...`;
- owner-scoped логи и owner-scoped job queue зафиксированы в документации.

### Канонические документы

Актуальными страницами для текущего состояния теперь считаются:

- `README.md`
- `docs/architecture.md`
- `docs/api.md`
- `docs/deployment.md`
- `02 Архитектура/Overview.md`
- `02 Архитектура/Architecture.md`
- `02 Архитектура/API.md`
- `02 Архитектура/Deployment.md`
- `02 Архитектура/Authentication.md`
- `02 Архитектура/Known Issues.md`

### Operational helper scripts

Под новый runtime-path обновлены:

- `tools/inspect_processed_sheet.py`
- `tools/fix_processed_sheet_status.py`

## Что переведено в historical context

Явные historical banners добавлены в:

- `05 Решения/2026-06-01 operational map current deployment.md`
- `05 Решения/2026-06-01 db and api inventory current sources.md`
- `01 Расследования/2026-06-08 tenant isolation логов и Google Sheets.md`

Это снижает риск, что старые заметки будут восприняты как текущая архитектурная правда.

## Что ещё остаётся как осознанный долг

### 1. Исторические заметки

В `01 Расследования/` и части `05 Решения/` всё ещё есть упоминания старой схемы путей и старого состояния deployment.

Это не баг документации, если:

- заметка явно воспринимается как historical context;
- текущие канонические страницы уже обновлены.

### 2. Partial snapshot

Workspace по-прежнему не является полным production repo:

- часть роутеров видна только по импортам;
- часть runtime-кода отсутствует локально;
- некоторые старые заметки ссылаются на surfaces, которые в workspace не раскрыты полностью.

### 3. Legacy compatibility code

В коде ещё временно сохраняется compatibility layer для старых runtime-secret путей.

Это осознанно, потому что:

- исторические payload могли хранить старые relative path значения;
- полное удаление compatibility logic без контрольного периода было бы рискованным.

## Главный вывод

На текущий момент критичный слой задачи выполнен:

- сервер работает на новой схеме;
- пользовательский регресс устранён;
- основная документация синхронизирована с live-состоянием;
- wiki приведена к текущей архитектуре;
- старые заметки отделены от канона хотя бы по самым рискованным точкам.

Оставшийся долг уже относится в основном к архиву расследований и неполному coverage snapshot, а не к тому, что текущая operational документация противоречит рабочей системе.
