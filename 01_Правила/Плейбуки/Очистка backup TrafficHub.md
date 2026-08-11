# Очистка backup TrafficHub

## Когда применять

Только по явному запросу владельца на очистку project-backups. Это data-risk операция.

## Канон

- Свежая локальная копия создаётся до удаления: `backups/TrafficHub_PostgreSQL_YYYY-MM-DD.sql.gz`.
- Перед очисткой обязательны равенство размера server/local и `gzip -t` локального файла.
- Удаляются только подтверждённые архивы TrafficHub: `/root/TrafficHub/data/backups`, `/root/TrafficHub/data/runtime/backups`, `/root/TrafficHub/backups`, `/root/TrafficHub_backups`, `/root/TrafficHub_backup_archive`, `/root/ssh-hardening-backups`.
- Не входят в scope: PostgreSQL/Redis volumes, `AccountManager/data/tdata_uploads`, `/var/backups` package-state, source worktrees.

## Проверка после операции

1. Ровно один локальный backup-файл.
2. `gzip -t` проходит.
3. В перечисленных server-каталогах `0` файлов.
4. `df -h /`, `docker compose ps`, `/api/health` подтверждают нормальное состояние.

## Зафиксированное выполнение

11.08.2026 создан `backups/TrafficHub_PostgreSQL_2026-08-11.sql.gz`; server project-backups очищены. Диск server: 70% до, 57% после.
