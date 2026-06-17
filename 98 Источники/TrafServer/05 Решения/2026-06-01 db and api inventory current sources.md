# 2026-06-01 db and api inventory current sources

## Анализ

Этот документ закрывает один из оставшихся `Partial`-слоёв из coverage audit: инвентарь БД, миграций и API-контуров по текущим локальным источникам.

Сразу важно развести источники:

1. `remote_server_snapshot`
- лучше отражает текущий server-side runtime и deploy-контур;
- но локально неполон по HTTP/API и части внутренних модулей.

2. `remote_files`
- шире покрывает API и `traffic_hub`;
- полезен как архитектурное зеркало;
- но не должен считаться 100% live source без revalidation.

Поэтому ниже каждый вывод относится либо к:
- `snapshot-confirmed`
- либо к `mirror-confirmed`
- либо к `partial due to source gap`

## Причина

### 1. В проекте подтверждены как минимум три независимых data-plane

#### A. Autolead runtime DB

- Статус: `snapshot-confirmed`
- Источник:
  - [utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py)
- Назначение:
  - локальный runtime-state Autolead loop
  - история отправок
  - retry lifecycle
  - run statistics

Подтверждённые таблицы:

- `leads`
- `send_history`
- `invite_history`
- `invite_message_state`
- `retry_queue`
- `run_log`
- `autofit_seen`
- `control_sync_queue`

Ключевые свойства:

- SQLite
- `PRAGMA journal_mode=WAL`
- owner-scoped фильтрация через `owner_username`
- часть drift/runtime-проблем уже связана именно с этими таблицами:
  - `run_log`
  - `retry_queue`
  - `leads`

#### B. Embedded control plane DB

- Статус: `snapshot-confirmed` по коду, `locally-proven` по [control.db](C:/Users/Арт/Desktop/TrafServer/control.db)
- Источник:
  - [control_store.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/control_store.py)
  - [control.db](C:/Users/Арт/Desktop/TrafServer/control.db)
- Назначение:
  - лицензии
  - shared/user configs
  - shared/user auth payloads
  - campaign sync/history

Подтверждённые таблицы в локальной БД:

- `license_users`
- `app_configs`
- `user_app_configs`
- `app_auth`
- `user_app_auth`
- `campaign_history`

Подтверждённые колонки показывают ownership split:

- HWID-scoped:
  - `app_configs`
  - `app_auth`
- login-scoped:
  - `user_app_configs`
  - `user_app_auth`
- mixed licensing metadata:
  - `license_users`

Это напрямую связано с уже подтверждёнными root causes:

- cross-user config drift
- shared/user ownership ambiguity
- `save_config()` side effects

#### C. TrafficHub business DB

- Статус: `mirror-confirmed`
- Источник:
  - [database.py](C:/Users/Арт/Desktop/TrafServer/remote_files/traffic_hub/models/database.py)
  - [migrations.py](C:/Users/Арт/Desktop/TrafServer/remote_files/traffic_hub/migrations.py)
  - `traffic_hub/alembic/versions/*`
- Назначение:
  - business entities TrafficHub
  - leads/offers/funnels/conversions/postbacks/finance/tools/users

Подтверждённые модели:

- `users`
- `leads`
- `messenger_accounts`
- `tool_run_sessions`
- `funnels`
- `offers`
- `network_integrations`
- `conversions`
- `network_offer_stats`
- `postback_logs`
- `payouts`
- `financial_records`

Ключевые свойства:

- async SQLAlchemy
- Alembic migrations
- `database_url` поддерживает SQLite для dev и PostgreSQL для prod
- tenant hardening отражён в миграциях `0005`–`0007`

### 2. Миграции TrafficHub подтверждают эволюцию tenant isolation

- Статус: `mirror-confirmed`
- Источник:
  - `traffic_hub/alembic/versions/0001_initial.py` ... `0007_owner_scoped_lead_adv_sub.py`

Что видно по миграциям:

1. `0001_initial`
- создаёт основной бизнес-набор таблиц

2. `0002_network_integrations`
- добавляет `network_integrations`

3. `0004_network_offer_stats`
- добавляет `network_offer_stats`

4. `0005_user_ownership`
- вносит `owner_username` и ownership-ограничения

5. `0006_tenant_hardening_shared_entities`
- усиливает owner-scoping и индексы по owner

6. `0007_owner_scoped_lead_adv_sub`
- отдельно пересобирает `leads` под owner-scoped уникальность

Вывод:

- tenant isolation здесь не “изначально встроен”, а добавлялся эволюционно;
- это хорошо согласуется с уже найденными forensic-следами drift и owner-binding проблем в других контурах.

### 3. API-контуры подтверждены минимум в трёх независимых слоях

#### A. Main Autolead API в `remote_files/api/routers`

- Статус: `mirror-confirmed`

Подтверждённые группы роутов:

- `jobs`
  - `/status`
  - `/run`
  - `/stop`
- `settings`
  - config/session/superjob/import-export/license-accounts
  - destructive clear-endpoints `/db/*`
- `offers`
  - vacancies/invites/import-export/binding/combined CRUD
- `leads`
  - listing/export/resend/messages
- `stats`
  - `summary`
  - `history`

Именно этот контур связан с:

- run status truthfulness
- settings import/export
- owner-scoped cleanup
- offer/config drift

#### B. TrafficHub API в `remote_files/traffic_hub`

- Статус: `mirror-confirmed`, но `partial source coverage`

`traffic_hub/app.py` включает роутеры:

- `auth`
- `integrations`
- `leads`
- `offers`
- `finance`
- `messengers`
- `funnels`
- `tracking`
- `postbacks`
- `stats`
- `tools`

Локально подтверждённые router-files в зеркале:

- `integrations`
- `leads`
- `offers`
- `postbacks`
- `stats`

Подтверждённые prefix'ы:

- `/traffic-api/settings/integrations`
- `/traffic-api/leads`
- `/traffic-api/offers`
- `/traffic-api/postbacks`
- `/traffic-api/stats`

Подтверждённые endpoint-группы:

- integrations test/sync/balance
- leads list/create/export/update
- offers list/create/update/delete
- stats KPI/charts/finance

Ограничение:

- часть импортируемых в `app.py` роутеров локально отсутствует в зеркале, значит API inventory для TrafficHub ещё не исчерпывающий.

#### C. AccountManager API

- Статус: `snapshot-confirmed`, `partial source coverage`
- Источник:
  - [AccountManager/api/main.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/AccountManager/api/main.py)

Подтверждено:

- отдельный FastAPI app
- отдельный health endpoint:
  - `/api/health`
- HTML/login endpoints:
  - `/`
  - `/login`
- подключаются роутеры:
  - `accounts`
  - `proxies`
  - `dashboard`
  - `gateway`
  - `management`
  - `content`

Ограничение:

- локально нет полного исходника `AccountManager/api/routers/*`, поэтому inventory маршрутов этого контура сейчас только частичный.

### 4. Compose подтверждает 4 persistence/DB surfaces

- Статус: `snapshot-confirmed`
- Источник:
  - [docker-compose.yml](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/docker-compose.yml)

Подтверждённые DB/storage paths:

- `DB_PATH=/app/data/autolead.db`
- `CONTROL_DB_PATH=/app/data/control.db`
- `DATABASE_URL=sqlite+aiosqlite:////app/data/traffic_dashboard.db`
- `AccountManager DB_PATH=sqlite:////app/data/accounts.db`

Вывод:

- проект живёт не на одной БД, а на наборе из отдельных SQLite/data surfaces;
- forensic-анализ по одной таблице или одному `.db` не может считаться полным автоматически.

## План исправления

Из этого inventory следуют практические выводы:

1. Для Autolead runtime-ветки основными таблицами остаются:
- `run_log`
- `retry_queue`
- `leads`
- `send_history`

2. Для config/ownership-ветки ключевой data-plane:
- `control.db`
- `app_configs`
- `user_app_configs`
- `app_auth`
- `user_app_auth`

3. Для будущих tenant/API расследований нужно отдельно учитывать TrafficHub business DB:
- SQLAlchemy models
- Alembic chain
- `/traffic-api/*` routers

4. Полная DB/API exhaustiveness всё ещё не 100%, потому что локальные источники неполны для:
- sender-module
- части TrafficHub routers
- части AccountManager routers

## Diff

Новый артефакт:

- [2026-06-01 db and api inventory current sources.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20db%20and%20api%20inventory%20current%20sources.md)

Эта заметка лучше всего читается вместе с:

- [2026-06-01 objective coverage audit.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20objective%20coverage%20audit.md)
- [2026-06-01 architecture map current server.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20architecture%20map%20current%20server.md)
- [2026-06-01 operational map current deployment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20operational%20map%20current%20deployment.md)

## Риски

Главные риски без такого inventory:

- перепутать `control.db` и `autolead.db` как будто это один и тот же слой;
- расследовать API только по одному зеркалу и считать картину полной;
- не заметить, что tenant hardening эволюционировал и поэтому старые drift-проблемы системны, а не случайны.

Оставшиеся ограничения:

- локально нет полного sender source;
- локально нет полного `AccountManager/api/routers/*`;
- `traffic_hub` router-set в зеркале частичный относительно `app.py`.

## Проверка после исправления

Этот inventory можно считать полезным, если теперь можно быстро ответить:

1. какая БД отвечает за какой контур;
2. какие таблицы уже подтверждены кодом или локальной SQLite;
3. какой API-контур относится к Autolead, TrafficHub и AccountManager;
4. где инвентарь полный, а где ещё только частичный.

На текущем шаге это условие выполнено.

## Дополнительные улучшения

Следующий самый полезный шаг по этой ветке:

1. собрать отдельный inventory именно по `AccountManager` data-model и router-set, если появится полный source;
2. добрать missing TrafficHub routers (`auth`, `finance`, `funnels`, `messengers`, `tracking`, `tools`);
3. затем обновить coverage audit и перевести DB/API ветку из `Partial` ближе к `Covered`.
> Historical note
>
> Эта заметка полезна как forensic snapshot на 1 июня 2026, но не как каноническая документация текущей системы.
> После миграции и infra-упрощения часть путей, storage-ролей и deployment-выводов устарела.
>
> Используйте вместо неё:
> - `README.md`
> - `docs/architecture.md`
> - `docs/api.md`
> - `docs/deployment.md`
> - `02 Архитектура/*`
