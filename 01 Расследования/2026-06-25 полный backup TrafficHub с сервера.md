# 2026-06-25 полный backup TrafficHub с сервера

## Симптом

Нужно сохранить полный backup TrafficHub с live-сервера на локальный компьютер в отдельную папку.

## Зона системы

- live server `150.241.70.31`
- server repo `/root/TrafficHub`
- containers:
  - `autolead_server_bot`
  - `traffichub_worker`
  - `traffichub_postgres`
  - `traffichub_redis`
  - `traffichub_caddy`
  - `traffichub_account_manager`
  - `traffichub_license_server`
  - `traffichub_license_auth`
  - `traffichub_standalone_content_bot`

## Гипотеза

Для восстановимого backup недостаточно скопировать только git repo. Нужны:

- архив `/root/TrafficHub`;
- manifest с commit/branch;
- состояние Docker;
- последние runtime-логи;
- PostgreSQL dump;
- Redis metadata.

## Проверка

Backup собран на сервере в архив:

```text
/tmp/traffichub_full_backup_2026-06-25_10-08-40.tar.gz
```

Скачан локально:

```text
C:\Users\Арт\Desktop\TrafficHub_Server_Backups\backup_2026-06-25_13-09-35\
```

Локальные файлы:

```text
traffichub_full_backup_2026-06-25_10-08-40.tar.gz
traffichub_full_backup_2026-06-25_10-08-40.tar.gz.sha256
```

## Наблюдение

Содержимое архива:

- `TrafficHub_repo.tar.gz`
- `MANIFEST.txt`
- `dumps/postgres_pg_dumpall.sql`
- `dumps/redis_info.txt`
- `meta/docker_ps.txt`
- `meta/docker_compose_ps.txt`
- `meta/docker_inspect.json`
- `meta/autolead_server_bot.last500.log`
- `meta/traffichub_worker.last500.log`
- `meta/git_status.txt`
- `meta/git_log_last20.txt`

Проверка целостности:

```text
SHA256: 6eff370421518aebd0cd1a4c3c5969cb8f6e710509c2db8607dc2e9556809e5f
MATCH: True
```

Server repo на момент backup:

```text
commit: 2231c4719
```

## Вывод

Backup успешно создан, скачан на локальный компьютер и проверен по SHA256.

Локальное место хранения не находится внутри Obsidian vault и не должно попадать в wiki sync:

```text
C:\Users\Арт\Desktop\TrafficHub_Server_Backups\backup_2026-06-25_13-09-35\
```

## Следующий шаг

- При восстановлении сначала распаковать внешний архив, затем `TrafficHub_repo.tar.gz`.
- PostgreSQL восстанавливать из `dumps/postgres_pg_dumpall.sql`.
- Docker/runtime состояние сверять по `meta/docker_ps.txt` и `meta/docker_inspect.json`.
- Если backup больше не нужен на сервере, можно удалить временные файлы из `/tmp`.

## Связанные заметки

- [[Runtime doctor]]
- [[TrafficHub deployed commit marker]]
- [[Infrastructure]]
