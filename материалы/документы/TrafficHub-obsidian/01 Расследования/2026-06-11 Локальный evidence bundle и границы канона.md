# 2026-06-11 Локальный evidence bundle и границы канона

Примечание:

- Эта заметка фиксирует состояние до live SSH sync `2026-06-11`.
- После подключения к серверу локальный `artifacts/remote_sync/docker-compose.yml` был переснят с live compose.
- Актуальный server-side итог см. в [[01 Расследования/2026-06-11 Live server sync и расхождения compose-access]].

## Симптом

- Wiki местами пишет о `/root/TrafficHub` так, будто полный checkout доступен локально и будто локальный `docker-compose.yml` уже подтверждает весь live-контур.

## Зона системы

- инженерная wiki;
- deployment/runtime evidence;
- локальный workspace `C:\Users\sergk\OneDrive\Desktop\traffichubserver`.

## Гипотеза

- Текущий workspace — не полный checkout `TrafficHub`, а evidence bundle из Obsidian wiki, server snapshot, partial compose и code fragments.
- Из-за этого часть страниц смешивает:
  - server snapshot от `2026-06-04`;
  - локальные кодовые фрагменты из `artifacts/remote_edit/*`;
  - реконструированные утверждения из legacy docs.

## Проверка

- В корне workspace нет директорий `api/`, `traffic_hub/`, `AccountManager/`, `dashboard/`; вместо них есть `artifacts/remote_edit`, `artifacts/remote_sync`, `wiki/TrafficHub-obsidian`, `license_server/`.
- `artifacts/remote_sync/docker-compose.yml` содержит сервис-блоки для:
  - `autolead_bot`
  - `license_auth`
  - `license_server`
  - `account_manager`
  - `caddy`
- Тот же compose snapshot подтверждает:
  - `DATABASE_URL=postgresql+asyncpg://traffichub:traffichub@postgres:5432/traffichub`
  - `POSTGRES_HOST=traffichub_postgres`
  - `CONTROL_SYNC_ENABLED`
  - `CONTROL_LEGACY_SHEETS_FALLBACK`
  - `CONTROL_LEGACY_SHEETS_DUAL_WRITE`
- `wiki/server-snapshot.md` с датой `2026-06-04` перечисляет контейнеры `traffichub_postgres`, `traffichub_redis`, `traffichub_worker`.
- `wiki/server-control-manifest.md` разрешает те же контейнеры для remote ops.
- `artifacts/remote_edit/api/server.py` подтверждает:
  - FastAPI app;
  - `SessionMiddleware` и `CORSMiddleware`;
  - `/api/health`;
  - `/ws/log` и `/ws/status`;
  - async background loops `_push_status_loop()` и `_partner_sync_loop()`;
  - redirect `GET /traffic*` -> `/` или `/#crm-finance`.
- `artifacts/remote_edit/api/ws_manager.py` подтверждает owner-scoped websocket log/status routing.
- `artifacts/remote_edit/traffic_hub/worker.py` подтверждает:
  - heartbeat file;
  - startup reconciliation stale job state;
  - single-active-job execution внутри процесса worker;
  - stop propagation по owner.
- Live re-check публичных health endpoints из этого workstation на `2026-06-11` не удался:
  - `traffic-hubcrm.ru/api/health` дал timeout;
  - `auth.traffic-hubcrm.ru/health` и `am.traffic-hubcrm.ru/api/health` упёрлись в TLS handshake/credentials timeout.

## Наблюдение

- На момент offline-проверки локально был только partial compose snapshot, а не полный live `docker-compose.yml`.
- Полный список контейнеров сейчас известен только как last confirmed snapshot на `2026-06-04`.
- Утверждение про `CONTROL_PG_LEGACY_IMPORT=false` не подтверждается доступным evidence bundle: этот ключ найден только в самой wiki.
- Старое описание отдельной `/traffic/` SPA устарело: локальный `api/server.py` явно редиректит `/traffic` обратно в основной dashboard.

## Вывод

- Для этой wiki нужно явно помечать источник каждого важного runtime-факта:
  - `local code fragment`;
  - `compose snapshot`;
  - `server snapshot 2026-06-04`;
  - `гипотеза`.
- `[[00-Project-Tree]]` нельзя трактовать как фактическое локальное дерево файлов; это реконструированная карта server repo.
- Утверждения про `worker` / `redis` / `postgres` остаются валидными только как last confirmed runtime snapshot, пока не получен новый live-срез.

## Следующий шаг

- При следующем доступе к live runtime заново снять:
  - `docker ps`
  - полный `docker compose config`
  - ответы `/api/health`
- Синхронизировать локальный `artifacts/remote_sync/docker-compose.yml` с сервером целиком, а не частичным срезом.
- После получения полного checkout перепроверить:
  - `traffic_hub/app.py`
  - `api/authz.py`
  - `traffic_hub/services/job_queue.py`
  - `traffic_hub/services/job_runner.py`
