# Docker

## Подтверждено

- контейнерный контур подтверждается live `docker-compose.yml` и `docker ps`;
- ключевые контейнеры: web/API, worker, PostgreSQL, Redis, license auth, license server, Account Manager, Caddy.

## Актуальный compose-контур

- `autolead_server_bot`
- `traffichub_worker`
- `traffichub_postgres`
- `traffichub_redis`
- `traffichub_license_auth`
- `traffichub_license_server`
- `traffichub_account_manager`
- `traffichub_caddy`

## Что важно

- старый compose-образ "autolead_bot + optional caddy" больше не описывает production целиком;
- worker health идёт по heartbeat file;
- `docker-compose.yml` является runtime source of truth для контейнерных зависимостей, а не старые how-to заметки.

## Глубокие ссылки

- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Контейнеры и сервисы|Контейнеры и сервисы]]
- [[материалы/документы/TrafficHub-obsidian/06-Deployment/Docker|Legacy Docker note]]

- [[материалы/документы/legacy-vault/01 Проекты/ТрафикХаб/Сервисы и контейнеры]]
