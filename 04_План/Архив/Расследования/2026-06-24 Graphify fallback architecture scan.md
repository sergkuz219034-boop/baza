# 2026-06-24 Graphify fallback architecture scan

## Симптом

- Нужно быстро получить карту актуального live-контура `TrafficHub` через канонический подход `Graphify`.
- В текущем Codex-чате `Graphify` не выдан как прямой callable tool, хотя в workspace есть следы его локального использования.

## Зона системы

- live repo: `/root/TrafficHub`
- wiki playbook: [[99_Архив/Исторические плейбуки/Graphify architecture scan]]
- архитектурные entrypoints: `api/server.py`, `traffic_hub/app.py`, `traffic_hub/worker.py`, `docker-compose.yml`

## Гипотеза

- Даже без прямого `Graphify` tool архитектурную карту можно подтвердить по live-коду и runtime-структуре.
- `Graphify` в этом проекте является навигационным ускорителем, а не обязательной runtime-зависимостью.

## Проверка

- Локально найдены артефакты `Graphify`:
  - `.claude/skills/graphify/.graphify_version`
  - [[99_Архив/Исторические плейбуки/Graphify architecture scan]]
  - старое расследование `2026-06-24 Graphify Runtime Inspector doctor timeline explain candidate`
- На live-сервере прочитаны:
  - `api/server.py`
  - `traffic_hub/app.py`
  - `traffic_hub/worker.py`
  - `docker-compose.yml`
- По live-дереву подтверждены основные каталоги: `api`, `dashboard`, `services`, `modules`, `traffic_hub`, `AccountManager`, `license_auth`, `license_server`, `standalone_content_bot`.

## Наблюдение

- `api/server.py` — главный live web-entrypoint `autolead_bot`.
- Он не заменяет `traffic_hub`, а встраивает его:
  - импортирует `init_traffic_hub`, `register_traffic_hub`, `shutdown_traffic_hub`;
  - одновременно подключает собственные роутеры `api/routers/*`.
- `traffic_hub/app.py` — отдельный product/API контур:
  - регистрирует `traffic_hub.api.routers.*`;
  - поднимает свой websocket `/traffic-ws` и `/ws`;
  - отвечает за migrations и async SQLAlchemy engine.
- `traffic_hub/worker.py` — отдельный owner-scoped worker contour:
  - читает queue из `traffic_hub.services.job_queue`;
  - спавнит `traffic_hub.job_process`;
  - ведёт heartbeat и восстанавливает stale job state после рестарта.
- `services/leads_service.py` и `modules/*` всё ещё активны и не могут считаться мёртвыми:
  - project использует bridge-подход, а не полный перенос логики в `traffic_hub/services/*`.
- `docker-compose.yml` подтверждает production contour:
  - `autolead_bot`
  - `worker`
  - `postgres`
  - `redis`
  - `license_auth`
  - `license_server`
  - `account_manager`
  - `caddy`
  - `standalone_content_bot`

## Вывод

- Каноническая архитектурная модель проекта сейчас гибридная:
  - web/dashboard/auth/live glue: `api/server.py` + `api/routers/*`
  - product/domain/API contour: `traffic_hub/*`
  - legacy business contour: `services/*`, `modules/*`, `utils/*`
  - async worker/queue contour: `traffic_hub/worker.py`, Redis, runtime state
  - infra contour: Docker Compose, PostgreSQL, Redis, Caddy, license services, AccountManager
- `Graphify` полезен как ускоритель навигации, но не заменяет live-подтверждение по коду и runtime.
- Для текущего чата архитектурная карта собрана подтверждённым fallback-способом.

## Следующий шаг

- Если в следующем чате будет доступен callable `Graphify`, использовать его поверх live snapshot только для ускорения навигации, а не как источник истины.
- При следующем крупном аудите отдельно разобрать границы между `api/*`, `traffic_hub/*` и legacy `services/modules`, потому что именно там накапливается основной архитектурный долг.
