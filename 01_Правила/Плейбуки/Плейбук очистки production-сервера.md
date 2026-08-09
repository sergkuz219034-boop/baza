# Плейбук очистки production-сервера

## Назначение

Безопасная очистка TrafficHub без потери PostgreSQL, Redis, Telegram-сессий и пользовательских изменений checkout.

## До очистки

1. Снять `git status`, `docker compose config --services`, `docker system df`, `df`.
2. Зафиксировать Docker volumes, размер `AccountManager/data/tdata_uploads` и контрольные счётчики БД.
3. Для каждого каталога проверить `realpath`, mounts, открытые файлы, процессы и dirty state.
4. Не удалять активные volumes, `tdata_uploads`, свежие backup и пользовательские изменения.

## Docker

- Канон: `deploy/traffichub_docker_maintenance.sh`.
- Сначала запускать `--dry-run`.
- Сохранять running image и один rollback для TrafficHub и Account Manager.
- Build cache сохранять в пределах 2 ГБ.
- Tagged-образ удалять только после проверки отсутствия контейнеров по ancestor/image ID.

## Journald, backup и tmp

- Journald ограничен `/etc/systemd/journald.conf.d/traffichub-retention.conf`: 500 МБ, 14 дней.
- PostgreSQL backup: штатные 14 дней из `deploy/traffichub_postgres_backup.sh`.
- Predeploy backup: 7 daily, 4 weekly, 6 monthly через `deploy/rotate_predeploy_backups.py`.
- `/tmp` очищать через `systemd-tmpfiles --clean`; не удалять каталог целиком.

## После очистки

1. Проверить все container health, `/api/health`, worker heartbeat.
2. Сверить volumes, `tdata_uploads` и контрольные счётчики БД.
3. Запустить runtime monitor вручную и после одного timer-цикла.
4. Сравнить `df`, `docker system df`, `journalctl --disk-usage`.

## Swap

Заполненный swap без активного swap-out не является самостоятельной аварией. Warning/Critical допустимы только вместе с низким `MemAvailable` или ненулевым swap-out.
