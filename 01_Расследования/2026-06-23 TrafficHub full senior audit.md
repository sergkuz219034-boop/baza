# 2026-06-23 TrafficHub full senior audit

## Статус

- Тип: доказательный Senior-аудит live-контура.
- Режим: 2026-06-23 аудит без изменения product-кода; 2026-06-24 переведено в режим исправления P1/P2.
- Источник истины: `/root/TrafficHub`, containers, PostgreSQL, Redis, live logs, tests, API/runtime.
- Техработы: включены в runtime container: `maintenance_mode=True`, `maintenance_message="Тех работы"`.

## Симптом

Проект активно чинится точечными фикcами, но часть проблем повторяется у разных пользователей: настройки, роли, postback sync, AccountManager, UI-состояния, Autolead flow. Требуется проверить не только `admin`, а весь общий контур для текущих и будущих пользователей.

## Зона системы

- web/API/dashboard: `api/server.py`, `api/routers/*`, `dashboard/*`
- embedded TrafficHub: `traffic_hub/app.py`, `traffic_hub/api/routers/*`
- worker/scheduler: `traffic_hub/worker.py`, `services/leads_service.py`
- runtime/business: `services/*`, `modules/*`, `utils/*`
- DB: PostgreSQL `traffichub`, Redis runtime keys
- integrations: Rabota.ru, Google Sheets, Leads.su, Lovko, SuperJob, Zarplata.ru, AccountManager
- infra: `docker-compose.yml`, Caddy, `autolead_server_bot`, `traffichub_worker`, `account_manager`

## Гипотеза

Основной риск не в одном баге UI, а в дрейфе границ: часть кода уже PostgreSQL/tenant-first, часть legacy-контуров ещё создаёт записи без обязательного owner/tenant context, а UI/API иногда скрывает это до live-синхронизации.

## Проверка

- `/root/TrafficHub`: `main`, `HEAD=5034c7b43`, worktree clean, remote `sergkuz219034-boop/TrafficHub`.
- GitHub checks для `5034c7b43`: `CI` success, `Build and Push Docker Image` success.
- Containers: `autolead_server_bot`, `traffichub_worker`, `traffichub_account_manager`, `postgres`, `redis`, `caddy`, license services running/healthy.
- Health: `/api/health` вернул `status=ok`, `control.backend=postgres`.
- Tests: `docker exec autolead_server_bot pytest -q` -> `310 passed, 43 skipped, 41 warnings`.
- PostgreSQL: `tenant_id` is `NOT NULL` в `conversions`, `financial_records`, `funnels`, `leads`, `messenger_accounts`, `network_integrations`, `network_offer_stats`, `offers`, `payouts`, `postback_logs`, `tenant_memberships`.
- Live logs: обнаружен `NotNullViolationError` по `postback_logs.tenant_id`.
- API smoke:
  - `/api/health` unauth -> `200`
  - `/api/settings` unauth -> `401`
  - `/api/settings/maintenance-mode` unauth -> `401`
  - `/traffic-api/settings/integrations` unauth -> `401`
  - `/api/account-manager/token` unauth -> `401`
  - `/account-manager/` unauth -> `500`

## Наблюдение

### P1: partner sync падает на `postback_logs.tenant_id NULL`

- Evidence: live log `autolead_server_bot`: `null value in column "tenant_id" of relation "postback_logs" violates not-null constraint`.
- Affected user in log: `artem`.
- File: `traffic_hub/api/routers/integrations.py::_import_network_conversions`.
- Cause: `PostbackLog(...)` создаётся без `tenant_id=tenant_id` и `owner_username=username`.
- Counterexample: `traffic_hub/api/routers/postbacks.py::_handle_postback` уже пишет `tenant_id=integration.tenant_id` и `owner_username=...`.
- Test gap: `tests/test_integrations_sync.py` проверяет `log.raw_data["source"]`, но не проверяет `log.tenant_id`; SQLite fixture не ловит live `NOT NULL`.
- Risk: sync Leads.su/Lovko может ломаться для любого пользователя с партнёрскими интеграциями.
- Fix plan: добавить `tenant_id` и `owner_username` в `_import_network_conversions`; добавить regression test на tenant/owner в `PostbackLog`; прогнать PostgreSQL-like или explicit assertion.
- Fix 2026-06-24: закрыто commit `3f42f069b`. `PostbackLog` теперь создаётся с `tenant_id` и `owner_username`; `tests/test_integrations_sync.py` проверяет tenant/owner для `Conversion`, `FinancialRecord`, `PostbackLog`.

### P1/P2: role drift между license-store и embedded TrafficHub DB

- Evidence:
  - `control_license_users`: `Artem=user`.
  - `users`: `Artem=admin`.
- Files: `traffic_hub/authz.py::ensure_license_user`, auth/session paths.
- Risk: если роль меняется в license contour, stale role в embedded DB может сохраняться до reauth/ensure-path.
- Fix plan: сделать синхронизацию роли обязательной на каждом защищённом запросе или добавить migration/repair job; добавить тест `license role downgrade updates users.role`.
- Fix 2026-06-24: live drift `Artem` исправлен (`control_license_users=user`, `users=user`). Код `ensure_license_user()` уже синхронизировал роль; добавлен regression `tests/test_traffic_authz_role_sync.py`.

### P2: `/account-manager/` unauth возвращает `500`

- Evidence: live probe `/account-manager/` -> `500`; прямой `http://account_manager:8000/` -> `401`.
- Traceback: `api/server.py:1317`, `TypeError: _account_manager_public_target() takes from 1 to 2 positional arguments but 3 were given`.
- Root cause: в `api/server.py` локальный wrapper `_account_manager_public_target(path, query)` конфликтует с импортированным helper signature; root/proxy routes вызывают его с `base_url, path, query`.
- Risk: не auth bypass, но внешний route даёт 500 вместо корректного redirect/401, ломает UX и мониторинг.
- Fix plan: исправить вызовы или имя wrapper; добавить test на `/account-manager/` и `/account-manager/{path}`.
- Fix 2026-06-24: закрыто commit `3f42f069b`. `/account-manager/` live smoke возвращает `302 Location: https://am.traffic-hubcrm.ru/`; добавлен `tests/test_account_manager_proxy_routes.py`.

### P2: model/nullability drift

- Evidence: live DB `tenant_id nullable=NO`, но `traffic_hub/models/database.py` содержит несколько `tenant_id = Column(..., nullable=True)`.
- Migration: `0009_tenant_scope.py` сделал backfill и `ALTER COLUMN tenant_id SET NOT NULL`.
- Risk: разработчик читает модель и думает, что `tenant_id` можно не передавать; это уже привело к P1.
- Fix plan: привести SQLAlchemy models к live constraints; добавить тест, запрещающий создание tenant-scoped entities без tenant.
- Fix 2026-06-24: закрыто commit `3f42f069b`. 11 tenant-scoped моделей переведены на `tenant_id nullable=False`; добавлен `tests/test_tenant_model_constraints.py`.

### P2: God modules и высокая связность

- Evidence largest files:
  - `services/leads_service.py` ~2839 lines.
  - `modules/platforms/lovko.py` ~1746 lines.
  - `utils/license.py` ~1422 lines.
  - `api/server.py` ~1328 lines.
  - `modules/sheets_sync.py` ~1257 lines.
  - `AccountManager/dashboard/app.js` ~1238 lines.
- Risk: точечный фикс легко ломает соседний сценарий; сложно доказать owner isolation для всех пользователей.
- Fix plan: не переписывать сразу; выделять owner context, job lifecycle, sheets sync и offer automation в отдельные small services с regression tests.

### P2/P3: DB hot-path требует отдельного index/query audit

- Evidence `pg_stat_user_tables` показал высокие scans на `users`, `autolead_app_log`, `control_user_app_auth`, `control_license_users`, `control_user_app_configs`.
- Indexes уже есть на `lower(login)` для control tables и owner/time для logs.
- Risk: проблема может быть не в отсутствии индекса, а в query pattern, polling и частоте обращений.
- Fix plan: включить `pg_stat_statements` или targeted query logging; оптимизировать только подтверждённые hot SQL.

### P3: deprecation debt

- Evidence full suite green, но `41 warnings`.
- Main groups: Pydantic V2 `class Config`, Starlette/FastAPI/httpx TestClient warnings, passlib `crypt`.
- Risk: обновление зависимостей может сломать тесты/validation без изменения бизнес-кода.
- Fix plan: отдельная maintenance задача, не смешивать с production bugs.

### P3: Redis runtime hygiene

- Evidence active job owners empty, но Redis содержит stale progress/state keys для `debug-worker-*`, `test-vbiv-owner`, `debuglogs`, `artem2`, `artemka` и старых owners.
- Risk: UI/status confusion при неправильном чтении stale state.
- Fix plan: добавить TTL/cleanup для debug/test progress keys; не удалять вручную без понимания owner state.

## Вывод

TrafficHub не выглядит сломанным целиком: runtime healthy, CI green, full pytest green, PostgreSQL-first контур подтверждён, owner-scoped модель в большинстве мест уже есть. Но для production-level использования есть P1/P2 риски: partner sync сейчас реально падает на live из-за `tenant_id`, AccountManager root route даёт 500, а role drift показывает, что auth/authz контуры ещё не полностью самовосстанавливающиеся.

## Оценки 0-10

| Категория | Оценка | Причина |
|---|---:|---|
| Архитектура | 6.5 | Контуры выделены, но legacy `services/modules/utils` всё ещё сильно связаны с новым `traffic_hub`. |
| Бизнес-логика Autolead | 6 | Много regression tests, но offer/platform automation и sheets flow остаются хрупкими. |
| Auth/authz/isolation | 5.5 | Owner/tenant модель есть, но найден role drift и tenant omission. |
| UI/UX | 6.5 | Основные сценарии есть, но `dashboard/app.js` слишком плотный и легко регрессирует. |
| Производительность | 6 | Runtime healthy, но hot scan/query pattern требует отдельного замера. |
| Security | 6 | Базовые unauth checks закрыты, но route 500 и role drift надо исправить. |
| DB | 6.5 | PostgreSQL-first подтверждён, но models не совпадают с live constraints. |
| Поддерживаемость | 5 | God modules и legacy boundaries увеличивают стоимость каждого фикса. |
| Production readiness | 6 | Подходит для controlled/internal use, но не для спокойного широкого production до закрытия P1/P2. |

## Technical debt table

| Priority | Debt | Evidence | Recommended action |
|---|---|---|---|
| P1 | `PostbackLog` создаётся без tenant/owner в partner sync | `integrations.py::_import_network_conversions`, live `NotNullViolationError` | Fix + regression test. |
| P1/P2 | Role drift `Artem=user` vs `users.Artem=admin` | `control_license_users`, `users` | Enforce role sync on protected paths. |
| P2 | `/account-manager/` 500 | `api/server.py:1317` TypeError | Fix wrapper/call signature + tests. |
| P2 | SQLAlchemy models say nullable while DB says NOT NULL | `traffic_hub/models/database.py`, live information_schema | Align model constraints. |
| P2 | High coupling in large modules | file sizes above | Extract by boundary after P1 fixes. |
| P2/P3 | Unknown hot SQL patterns | scans + existing indexes | Add query-level evidence before optimizing. |
| P3 | Deprecation warnings | `pytest` warnings | Dependency maintenance pass. |

## Roadmap

### 1-2 дня

- Fix `PostbackLog tenant_id/owner_username` in partner sync.
- Fix `/account-manager/` route 500.
- Add regression tests for both.
- Repair role drift for `Artem` and add role-sync regression.
- Re-run `pytest -q`, push, deploy, verify `/api/health`.

### Среднесрочно

- Align SQLAlchemy model nullability with migrations.
- Add tenant/owner invariant tests for every tenant-scoped entity.
- Add debug cleanup/TTL for stale Redis progress keys.
- Split AccountManager proxy tests from dashboard navigation tests.

### Крупные изменения

- Разрезать `services/leads_service.py` на pipeline stages: collect, sheets export, send, retry, status close.
- Разрезать `dashboard/app.js` на модули state/API/render.
- Вынести platform automation contract: required fields, submit detection, confirmation detection, debug artifacts.
- Включить query-level performance telemetry before DB optimization.

## Выпускать ли в продакшен сейчас

Для закрытого controlled use можно продолжать. P1/P2 из этого audit закрыты и запушены в `TrafficHub` commit `3f42f069b`; остаются P2/P3 задачи по декомпозиции крупных модулей, query-level performance audit, deprecation debt и Redis runtime hygiene.

## Следующий шаг

После закрытия P1/P2: дождаться GitHub checks для `3f42f069b`, затем отдельно планировать P2/P3 maintenance без смешивания с production bugs.
