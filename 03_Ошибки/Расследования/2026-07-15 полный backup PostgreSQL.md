# 2026-07-15 полный backup PostgreSQL

## Симптом

В `data/backups/` не было свежего полного production dump PostgreSQL: последние SQL-файлы от 21 июня были точечными cleanup-артефактами. Регулярного scheduler не было.

## Зона системы

- `/root/TrafficHub/data/backups/`
- `deploy/traffichub_postgres_backup.sh`
- `/etc/systemd/system/traffichub-postgres-backup.{service,timer}`
- контейнер `traffichub_postgres`

## Гипотеза

Pre-deploy backup в `deploy/remote_deploy.sh` защищает только отдельные deployments и не заменяет независимый регулярный backup.

## Проверка

- Live PostgreSQL healthy, размер БД: 106 MB; свободно 26 GB.
- До исправления `systemctl list-timers` не находил TrafficHub backup timer.
- Последние SQL-файлы `alice_cleanup_20260621_*.sql` — точечные, а не полный dump.
- После исправления service вручную завершился `Result=success`; timer enabled и ожидает следующий запуск.

## Наблюдение

Созданы свежие наборы `20260715T095942Z` и `20260715T100148Z`: полный production `sql.gz`, globals `sql.gz`, SHA-256 manifest. Каждый архив прошёл `gzip -t`; скрипт использует полный `pg_dump` без table filters и `pg_dumpall --globals-only`.

## Вывод

Риск отсутствия свежего полного backup и регулярного расписания устранён на live. Product commit: `83d5cab8b` (`ops: schedule full postgres backups`).

## Следующий шаг

Настроить offsite копирование зашифрованных backup-наборов: текущий контур хранит их только на этом host и не переживёт его полную потерю.
