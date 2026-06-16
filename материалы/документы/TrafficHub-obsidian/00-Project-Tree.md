# Карта checkout и runtime

Это не фактическое дерево локального workspace.

- Локальный workspace содержит:
  - Obsidian wiki
  - server snapshots
  - partial/live copies отдельных файлов
  - синхронизированный `artifacts/remote_sync/docker-compose.yml`
- Полный checkout проекта живёт на сервере в `/root/TrafficHub`.
- Ниже — реконструированная карта server checkout, сверенная с live SSH sync `2026-06-11`.

## 1. Server checkout `/root/TrafficHub`

```text
TrafficHub/
├── main.py
├── Dockerfile
├── docker-compose.yml
├── README.md
├── CHANGELOG.md
├── config/
│   └── settings.py
├── api/
│   ├── server.py
│   ├── authz.py
│   ├── autolead_access.py
│   ├── ws_manager.py
│   └── routers/
│       ├── jobs.py
│       ├── leads.py
│       ├── stats.py
│       ├── settings.py
│       ├── offers.py
│       ├── system.py
│       ├── debug.py
│       ├── avito.py
│       └── control.py
├── services/
│   ├── leads_service.py
│   └── stats_service.py
├── modules/
│   ├── rabota_api.py
│   ├── sheets_sync.py
│   ├── vbiv_bot.py
│   ├── avito_import.py
│   ├── superjob/
│   │   └── scraper.py
│   └── platforms/
│       ├── leadsu.py
│       ├── lovko.py
│       ├── tilda.py
│       └── base.py
├── utils/
│   ├── database.py
│   ├── control_store.py
│   ├── control_sync.py
│   ├── license.py
│   ├── access.py
│   ├── state.py
│   ├── runtime_logging.py
│   ├── config_loader.py
│   ├── startup_check.py
│   └── data_processor.py
├── traffic_hub/
│   ├── app.py
│   ├── worker.py
│   ├── migrations.py
│   ├── api/
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── leads.py
│   │       ├── offers.py
│   │       ├── finance.py
│   │       ├── messengers.py
│   │       ├── funnels.py
│   │       ├── tracking.py
│   │       ├── postbacks.py
│   │       ├── stats.py
│   │       ├── tools.py
│   │       └── integrations.py
│   ├── services/
│   │   ├── job_queue.py
│   │   └── job_runner.py
│   └── models/
├── dashboard/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── modules/
├── license_auth/
├── license_server/
├── AccountManager/
│   ├── api/
│   ├── dashboard/
│   ├── database/
│   ├── services/
│   └── data/
├── deploy/
│   └── Caddyfile
├── tests/
├── wiki/
├── data/
│   ├── runtime/
│   ├── logs/
│   ├── debug/
│   └── backups/
└── secrets/
```

## 2. Что за что отвечает

- `api/`
  - основной FastAPI entrypoint dashboard/API
  - `/api/*`, `/auth/*`, `/ws/*`
- `services/`
  - orchestration слой Autolead
  - полный цикл, сбор, экспорт, рассылка
- `modules/`
  - внешние интеграции и платформы
  - Rabota API, Google Sheets, Playwright autofill, партнёрские лендинги
- `utils/`
  - shared runtime infrastructure
  - control store, sqlite-backed lead storage, state, config merge, logging
- `traffic_hub/`
  - embedded TrafficHub domain/API
  - `/traffic-api/*`
  - Redis job queue contract
  - отдельный worker process
- `dashboard/`
  - основной frontend dashboard
- `license_auth/`, `license_server/`
  - auth/license контур
- `AccountManager/`
  - отдельное приложение внутри монорепозитория
- `deploy/`
  - reverse proxy config
- `data/`
  - runtime state и persistent artifacts

## 3. Runtime layout в контейнерах

Подтверждено live `docker-compose.yml`.

```text
/app/data/
├── runtime/
│   ├── autolead.db
│   ├── control.db
│   ├── traffic_dashboard.db
│   ├── worker.heartbeat
│   ├── autolead_access.json
│   └── secrets/
│       ├── config.json
│       ├── rabota_tokens.json
│       ├── service_account.json
│       └── service_account__<owner>.json
├── logs/
│   └── autolead.log
├── debug/
│   └── debug_*.png / debug_*.html
└── backups/
```

Что важно:

- `control.backend=postgres` уже живой факт.
- Но legacy SQLite runtime ещё не исчез:
  - `autolead.db`
  - `control.db`
  - `traffic_dashboard.db`
- Следовательно “полный переход на PostgreSQL” для всего продукта ещё не завершён.

## 4. Container-to-code mapping

- `autolead_server_bot`
  - код: `api/server.py`, `services/*`, `modules/*`, `traffic_hub/app.py`
- `traffichub_worker`
  - код: `traffic_hub/worker.py`, `traffic_hub/services/job_queue.py`, `traffic_hub/services/job_runner.py`
- `traffichub_postgres`
  - primary DB для PostgreSQL-backed control и `traffic_hub`
- `traffichub_redis`
  - queue/state/event bus для jobs
- `traffichub_license_auth`
  - auth issuer service
- `traffichub_license_server`
  - license API
- `traffichub_account_manager`
  - код: `AccountManager/*`
- `traffichub_caddy`
  - код: `deploy/Caddyfile`

## 5. Что устарело в старом tree

- `dashboard/traffic/` нельзя трактовать как active standalone SPA.
  - Live `api/server.py` редиректит `/traffic*` обратно в основной dashboard.
- `utils/database.py` и `utils/control_store.py` нельзя описывать как “исторические” или “полностью migrated”.
  - Они всё ещё участвуют в runtime.
- `00-Project-Tree` не должен восприниматься как доказательство наличия файлов локально.
  - Это карта server checkout, а не local filesystem inventory.

## 6. См. также

- [[материалы/документы/TrafficHub-obsidian/02 Архитектура/00 Обзор]]
- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Контейнеры и сервисы]]
- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Control Store]]
- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Job Queue]]
- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Auth и Access]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-11 Live server sync и расхождения compose-access]]
