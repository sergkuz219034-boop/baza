# Operational Map: Current Deployment

Дата: 2026-06-01
Источник фактов:

- live `docker ps`
- `docker-compose.yml`
- `deploy/Caddyfile`
- live `.env` (значения секретов намеренно не реплицируются в заметку)

## Анализ

### Контейнеры и порты

Подтверждены live-контейнеры проекта:

- `autolead_server_bot`
  - image: `traffichub-autolead_bot`
  - status: `healthy`
  - bind: `127.0.0.1:8080 -> 8080`
- `traffichub_license_auth`
  - image: `traffichub-license_auth`
  - status: `healthy`
  - bind: `127.0.0.1:8400 -> 8400`
- `traffichub_account_manager`
  - image: `traffichub-account_manager`
  - status: `healthy`
  - bind:
    - `127.0.0.1:8124 -> 8000`
    - `0.0.0.0:1443 -> 1443`
- `traffichub_caddy`
  - image: `caddy:2-alpine`
  - bind:
    - `0.0.0.0:80 -> 80`
    - `0.0.0.0:443 -> 443`

Дополнительно на сервере живут посторонние контейнеры (`searxng-local`, `amnezia-xray`, `mfo_api`), но они не относятся к текущему TrafficHub deployment.

### Домены и reverse proxy

Подтверждено:

- `PUBLIC_DOMAIN` -> основной Autolead / TrafficHub dashboard
- `LICENSE_AUTH_DOMAIN` -> отдельный auth service
- `ACCOUNT_MANAGER_DOMAIN` -> AccountManager
- `AI_AGENT_DOMAIN` -> отдельный AI-agent perimeter

По `Caddyfile`:

- `PUBLIC_DOMAIN` проксируется в `autolead_bot:8080`
- `LICENSE_AUTH_DOMAIN` проксируется в `license_auth:8400`
- `ACCOUNT_MANAGER_DOMAIN` проксируется в `account_manager:8000`
- `AI_AGENT_DOMAIN` имеет `basic_auth` и `redir`

### Хранилища данных

Подтверждено по compose:

- `autolead_bot`
  - `/app/data/autolead.db`
  - `/app/data/control.db`
  - `/app/data/traffic_dashboard.db`
  - `/app/secrets/*`
- `license_auth`
  - `/app/data/control.db`
  - `/app/secrets/*`
- `account_manager`
  - `/app/data/accounts.db`
  - `/app/secrets/*` (read-only)

### Auth boundaries

Подтверждены разные auth boundary:

- локальный session/auth слой Autolead
- external auth через `license_auth`
- `AccountManager` со своим `SESSION_SECRET_KEY`
- reverse proxy perimeter в `Caddy`

## Причина

### 1. Security drift в perimeter уже подтверждён operational-картой

- Описание проблемы: `ACCOUNT_MANAGER_BASIC_AUTH_*` заданы в `.env` и compose, но не используются в `Caddyfile`.
- Первопричина: reverse proxy конфиг не соответствует декларируемому env/compose contract.
- Критичность: `Low/Medium`
- Возможные последствия:
  - ложное чувство защищённости;
  - операторы могут считать AccountManager защищённым basic auth, хотя это не так.
- Рекомендуемое исправление:
  - либо реально включить `basic_auth`;
  - либо удалить мёртвую конфигурацию.

### 2. Секреты и токены хранятся в `.env` в plaintext

- Описание проблемы: live `.env` содержит множество боевых секретов, токенов и внешних credential entries в открытом виде.
- Первопричина: deployment опирается на flat env-file как на универсальное хранилище секретов.
- Критичность: `Critical`
- Возможные последствия:
  - компрометация внешних интеграций;
  - lateral movement между подсистемами;
  - быстрый захват auth/perimeter при утечке файла.
- Подтверждённые категории secrets:
  - session/auth secrets;
  - external auth key paths/config;
  - basic auth hash values;
  - API tokens;
  - Telegram credentials;
  - LLM/API provider secrets;
  - внешние partner credentials.
- Рекомендуемое исправление:
  - вынести высокочувствительные secrets из `.env`;
  - разделить secrets по подсистемам;
  - использовать отдельное защищённое secret storage или как минимум root-only managed env files с минимальным объёмом.

### 3. Один deployment содержит несколько security contexts

- Описание проблемы: в одной инсталляции сосуществуют Autolead, License Auth, AccountManager и AI perimeter.
- Первопричина: монорепо + единый compose + единый `.env`.
- Критичность: `Medium`
- Возможные последствия:
  - один leaked env-file открывает сразу несколько контуров;
  - сложно проводить ротацию по частям.
- Рекомендуемое исправление:
  - разделить secrets и env surface по сервисам;
  - уменьшить blast radius каждого файла конфигурации.

## План исправления

1. Не публиковать и не копировать live `.env` в wiki или локальные заметки.
2. Зафиксировать secret sprawl как отдельную root cause.
3. Затем:
   - отделить базовые app settings от высокочувствительных токенов;
   - разнести secrets по сервисам;
   - провести ротацию критичных credential classes.

## Diff

Код и deployment не менялись.

Добавлен документ:

- `05 Решения/2026-06-01 operational map current deployment.md`

Почему это безопасно:

- заметка не раскрывает сами значения секретов;
- она фиксирует классы рисков и контуры deployment.

## Риски

- Если продолжать хранить весь security material в одном `.env`, любой доступ к файлу эквивалентен широкому компромиссу deployment.
- Reverse proxy drift вокруг AccountManager остаётся источником неверных operational предположений.

## Проверка после исправления

На этом этапе проверка уже выполнена через:

- live `docker ps`
- `docker-compose.yml`
- `deploy/Caddyfile`
- live `.env` inspection без репликации значений в документации

## Дополнительные улучшения

- Следующий полезный шаг: сделать redacted inventory секретов по классам и по сервисам, без значений.
- После этого можно приоритизировать ротацию по blast radius, а не “всё сразу”.
> Historical note
>
> Эта заметка описывает состояние deployment на 1 июня 2026.
> После 7-8 июня 2026 она больше не отражает текущую каноническую схему.
> Актуальные источники:
> - `remote_server_snapshot/docker-compose.yml`
> - `docs/deployment.md`
> - `02 Архитектура/Deployment.md`
>
> Ключевые изменения после этой заметки:
> - `control.db` перестал быть primary source, control store стал PostgreSQL-first;
> - runtime storage разделён на `data/runtime`, `data/logs`, `data/debug`, `data/backups`;
> - runtime-secrets вынесены в `data/runtime/secrets`;
> - `worker` выделен как отдельный контейнер с heartbeat-healthcheck;
> - отдельная `account_manager_net` удалена, используются `core_net` и `edge_net`.
