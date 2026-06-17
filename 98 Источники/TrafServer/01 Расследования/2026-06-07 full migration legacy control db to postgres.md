# Полная миграция legacy `control.db` в PostgreSQL

## Симптом

`TrafficHub` уже использовал PostgreSQL для основного auth и доменных сущностей, но `control.db` оставался отдельным источником правды для:

- `license_users`
- `app_configs`
- `user_app_configs`
- `user_app_auth`
- `app_auth`
- `campaign_history`

Из-за этого появлялся split-brain:

- часть пользователей жила только в `control.db`
- runtime-профили и секреты были только в SQLite
- перерегистрация и логин могли расходиться между SQLite и Postgres

## Зона системы

- `utils/control_store.py`
- `utils/license.py`
- `/root/TrafficHub/docker-compose.yml`
- `traffichub_postgres`
- `autolead_server_bot`
- `traffichub_worker`
- `traffichub_license_auth`

## Гипотеза

Если перенести legacy-таблицы в отдельный Postgres namespace и перевести `control_store` на Postgres-first backend, то:

- исчезнет второй источник правды;
- auth/runtime начнут читать единое состояние;
- `control.db` можно будет оставить только как исторический snapshot.

## Проверка

1. Считана живая схема `control.db` внутри `autolead_server_bot`.
2. Считаны текущие Postgres-таблицы и runtime `users`.
3. Подтверждено, что в SQLite есть данные, которых нет в Postgres, например `alice`.
4. В `utils/control_store.py` добавлен Postgres backend с таблицами:
   - `control_license_users`
   - `control_app_configs`
   - `control_user_app_configs`
   - `control_user_app_auth`
   - `control_app_auth`
   - `control_campaign_history`
5. Добавлена миграция из SQLite в Postgres и синхронизация `license_users -> users`.
6. `license_auth` получил `DATABASE_URL`, чтобы auth-слой тоже работал через Postgres.
7. Пересобраны и перезапущены:
   - `autolead_server_bot`
   - `traffichub_worker`
   - `traffichub_license_auth`
8. После первого запуска миграция переведена в one-shot режим, чтобы SQLite больше не перетирал новые данные в Postgres.

## Наблюдение

- `control_store.health()` теперь возвращает `backend=postgres`.
- Счётчики после миграции совпали:
  - `control_license_users = 6`
  - `control_app_configs = 1`
  - `control_user_app_configs = 12`
  - `control_user_app_auth = 3`
  - `control_app_auth = 1`
  - `control_campaign_history = 3316`
- Пользователь `alice`, который раньше был только в SQLite, появился в Postgres `users`.
- `traffichub_license_auth` подтверждает `_postgres_license_enabled() == True`.

## Вывод

Канонический runtime для legacy control-данных переведён на PostgreSQL.

`control.db` больше не должен рассматриваться как основной storage. Он остаётся:

- как исторический backup;
- как источник только для однократного импорта в новых окружениях, где Postgres-таблицы ещё пусты.

## Следующий шаг

- отдельным шагом можно отключить или архивировать `control.db` после контрольного периода;
- стоит зафиксировать `control_*` таблицы в архитектурной документации как transitional runtime-layer, а не как постоянный публичный контракт.

## Дополнение после cleanup

- В `docker-compose.yml` включён `CONTROL_PG_LEGACY_IMPORT=false` по умолчанию.
- Быстрый `/api/health` теперь возвращает:
  - `control.backend`
  - `control.legacy_import_enabled`
  - `control.ok`
- Это означает, что прод больше не зависит от live-чтения `control.db` при каждом старте. SQLite остаётся на диске только как legacy artifact.
