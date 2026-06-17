# Documentation resync after container simplification

Теги: #решение #документация

## Что обнаружено

### 1. Документация отставала от live compose

- Где найдено: `README.md`, `docs/deployment.md`, `docs/architecture.md`
- Почему устарело: страницы всё ещё описывали укрупнённую старую схему с `autolead_bot`, `license_auth`, `account_manager`, `caddy`, но без `worker`, `postgres`, `redis`, `license_server`
- Как на самом деле: актуальный live deployment включает восемь сервисов TrafficHub и две основные сети

### 2. Старый storage layout был описан как `./data + ./secrets`

- Где найдено: `README.md`, `docs/deployment.md`
- Почему устарело: после последних infra-изменений runtime больше не хранит все секреты в одном каталоге
- Как на самом деле: `data/runtime/secrets/` теперь отделён от системного `secrets/`

### 3. В документации не было worker health-модели

- Где найдено: `README.md`, `docs/architecture.md`, `docs/deployment.md`
- Почему устарело: раньше worker считался просто фоновым контейнером без явного признака живости
- Как на самом деле: worker поддерживает heartbeat и Docker healthcheck

### 4. Не была зафиксирована упрощённая сеть

- Где найдено: `README.md`, `docs/deployment.md`
- Почему устарело: старая схема не отражала удаление отдельной `account_manager_net`
- Как на самом деле: сейчас используются `core_net` и `edge_net`

## Что обновлено

- обновлён `README.md`
- обновлён `docs/architecture.md`
- обновлён `docs/deployment.md`
- обновлён `CHANGELOG.md`
- создана ADR/infra-заметка `2026-06-08 container topology simplification and health model.md`

## Какие страницы созданы

- `05 Решения/2026-06-08 container topology simplification and health model.md`
- `05 Решения/2026-06-08 documentation resync after container simplification.md`

## Какие страницы изменены

- `README.md`
- `CHANGELOG.md`
- `docs/architecture.md`
- `docs/deployment.md`

## Что ещё отсутствует или требует следующей волны

- страница `docs/api.md` ещё не пересобрана под текущую live-правду по worker/job queue и owner-scoped логам
- часть Obsidian-страниц в `02 Архитектура` и `04 Сущности` ещё ссылается на старую модель `secrets/config.json`
- старые заметки в `wiki/` и некоторых `05 Решения/*` содержат допущения эпохи до разделения runtime-secrets

## Рекомендация

Следующая волна должна пройтись по wiki-страницам про Config, Deployment, Control Store, Authentication и Troubleshooting и заменить старую схему `secrets/config.json` на фактическую `data/runtime/secrets/config.json`, не трогая при этом страницы, где речь идёт именно о системных ключах установки.
