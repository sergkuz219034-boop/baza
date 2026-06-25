# 2026-06-25 единый полный backup TrafficHub

## Симптом

Нужен один полный backup TrafficHub с сервера на локальный компьютер, а не только частичный snapshot repo/dump.

## Зона системы

- live server `150.241.70.31`
- repo `/root/TrafficHub`
- Docker Compose контур TrafficHub
- Docker volumes:
  - `traffichub_caddy_config`
  - `traffichub_caddy_data`
  - `traffichub_postgres_data`
  - `traffichub_redis_data`
- Docker images:
  - `caddy:2-alpine`
  - `postgres:16-alpine`
  - `redis:7-alpine`
  - `traffichub-account_manager`
  - `traffichub-autolead_bot`
  - `traffichub-license_auth`
  - `traffichub-license_server`
  - `traffichub-standalone_content_bot`
  - `traffichub-worker`

## Гипотеза

Для полноценного переносимого backup нужен один архив, который содержит:

- полный repo `/root/TrafficHub` вместе с `.git`;
- logical PostgreSQL dump;
- raw PostgreSQL/Redis/Caddy volumes;
- Docker image exports;
- Docker/container/network metadata;
- последние runtime-логи;
- compose config;
- manifest и inventory.

## Проверка

Финальный локальный путь:

```text
C:\Users\Арт\Desktop\TrafficHub_FULL_Server_Backups\FULL_backup_2026-06-25_13-30-38\
```

В папке оставлены только:

```text
traffichub_FULL_single_backup_2026-06-25_10-17-30.tar.gz
traffichub_FULL_single_backup_2026-06-25_10-17-30.tar.gz.sha256
```

Размер архива:

```text
5121401377 bytes
```

SHA256:

```text
e440136f14157828db14c225e36b4a34f9058151ce2f3b151cadfa773009415b
```

Проверка:

```text
MATCH=True
```

## Наблюдение

Первичная попытка финальной упаковки поймала изменение `traffichub_postgres_data.tar.gz` во время чтения, потому что сервисы были запущены.

Для консистентного raw-volume snapshot контейнеры были коротко остановлены через `docker compose stop`, volumes пересняты, затем контур поднят через `docker compose up -d`.

После операции контейнеры:

- `traffichub_worker` — healthy;
- `autolead_server_bot` — healthy;
- `traffichub_postgres` — healthy;
- `traffichub_account_manager` — healthy;
- `traffichub_license_server` — healthy;
- `traffichub_license_auth` — healthy;
- `traffichub_redis` — healthy;
- `traffichub_caddy` — running;
- `traffichub_standalone_content_bot` — running.

## Содержимое архива

Верхний уровень:

- `MANIFEST.txt`
- `INVENTORY.txt`
- `repo/root_TrafficHub_full.tar.gz`
- `dumps/postgres_pg_dumpall.sql`
- `dumps/redis_info_keys_sample.txt`
- `volumes/*.tar.gz`
- `images/*.image.tar.gz`
- `images/*.inspect.json`
- `meta/*`
- `system/docker-compose*.yml`
- `system/systemd_related_services.txt`
- `system/root_crontab.txt`

## Вывод

Единый полный backup TrafficHub создан, скачан на локальный компьютер, проверен по SHA256 и структурно проверен без распаковки.

Временные архивы и части в `/tmp` на сервере удалены после успешной локальной проверки.

## Следующий шаг

Для восстановления:

1. Проверить SHA256.
2. Распаковать внешний архив.
3. Восстановить repo из `repo/root_TrafficHub_full.tar.gz`.
4. При необходимости загрузить Docker images через `docker load`.
5. Восстановить volumes из `volumes/*.tar.gz`.
6. Восстановить PostgreSQL logical dump из `dumps/postgres_pg_dumpall.sql`, если raw volume не используется.
7. Сверить compose/system состояние по `meta` и `system`.

## Связанные заметки

- [[Runtime doctor]]
- [[Infrastructure]]
- [[Deployment]]
