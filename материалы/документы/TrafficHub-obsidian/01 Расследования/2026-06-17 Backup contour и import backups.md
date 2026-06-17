# 2026-06-17 Backup contour и import backups

## Симптом

- страница `[[05_Эксплуатация/Резервные копии]]` указывала устаревший backup path и не различала system backups и import backups.

## Зона системы

- system backup API
- settings/offers import backups
- retention

## Гипотеза

- основной system backup живёт внутри repo-root в `backups/`, а не в `/root/TrafficHub_backups`;
- import backups для настроек и офферов живут отдельно в `data/backups`;
- cleanup старого `/root/TrafficHub_backup_archive` не отменяет наличие активного code-backed backup contour.

## Проверка

- просмотрен live source tree `/root/TrafficHub`:
  - `api/routers/system.py`
  - `api/routers/settings.py`
  - `api/routers/offers.py`
  - `api/routers/settings_bundle.py`
  - `tests/test_system_backups.py`
  - `tests/test_settings_import_export.py`
  - `tests/test_offers_import_export.py`

## Наблюдение

- `api/routers/system.py`:
  - `_backup_root()` создаёт каталог `repo_root/backups`;
  - system backup files называются `traffichub-backup-*.zip`;
  - `_backup_keep_count()` читает retention из `TRAFFICHUB_BACKUP_KEEP`, default `5`;
  - `_prune_old_backups()` удаляет старые zip archives сверх retention;
  - backup delete-path валидирует имя и запрещает выход за `backups/`.
- `tests/test_system_backups.py` подтверждает:
  - `POST /api/system/backups` создаёт backup;
  - retention pruning реально работает;
  - delete backup требует admin и валидирует имя архива.
- `api/routers/offers.py`:
  - import офферов создаёт `offers-import-backup-*.json`.
- `api/routers/settings_bundle.py` + `tests/test_settings_import_export.py`:
  - import настроек создаёт `settings-import-backup-*.json` в `data/backups`;
  - backup включает предыдущий config и secrets files.
- old `/root/TrafficHub_backup_archive` уже удалён на live host как лишний архивный слой, но это не равно удалению active backup logic из приложения.

## Вывод

- канонический backup contour надо делить на два класса:
  - system backups: `repo_root/backups/traffichub-backup-*.zip`
  - import backups: `data/backups/settings-import-backup-*.json` и `data/backups/offers-import-backup-*.json`
- старый внешний archive layer больше не канон; канон — это active code-backed backup mechanisms.

## Следующий шаг

- обновить `[[05_Эксплуатация/Резервные копии]]`;
- при следующем operational расследовании сначала различать zip system backup и JSON import backup.
