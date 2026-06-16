# 2026-06-15 Первый decomposition step `api.routers.settings` на `settings_bundle`

## Симптом

`api/routers/settings.py` был крупным mixed-router файлом и одновременно держал:

- import/export bundle настроек;
- runtime patch настроек;
- Google Sheets helpers;
- upload `service_account.json`;
- database cleanup endpoints;
- Rabota OAuth/token flow.

При этом import/export bundle helper-блок был почти полностью независим от остальных зон и уже имел прямое test coverage.

## Зона системы

- `api/routers/settings.py`
- import/export настроек
- secrets bundle
- backup/import path

## Гипотеза

Bundle helper-логику можно безопасно вынести в отдельный модуль, если:

- сохранить router endpoints без изменений;
- передавать `BASE_DIR`, `load_config` и текущего пользователя явно;
- не менять формат export/import payload.

## Проверка

Подтверждено на live source of truth `/root/TrafficHub`:

- создан `api/routers/settings_bundle.py`;
- из `api/routers/settings.py` вынесены:
  - `secrets_dir`
  - `backups_dir`
  - `iter_exportable_secret_files`
  - `read_secret_bundle`
  - `build_settings_export_payload`
  - `backup_settings_bundle`
  - `normalize_settings_import_payload`
  - `write_imported_secret_files`
  - `sync_imported_auth_secrets`

Проверки:

- `python3 -m compileall -q api/routers/settings_bundle.py api/routers/settings.py`
- `docker exec autolead_server_bot python -m pytest -q tests/test_settings_import_export.py tests/test_auth_roles.py tests/test_proxy_config.py tests/test_sheets_queues.py`

## Наблюдение

- `api/routers/settings.py` сократился до `905` строк.
- `api/routers/settings_bundle.py` содержит `152` строки.
- Прямой тестовый набор по import/export и смежным patch/helper path остаётся зелёным после выноса.

## Вывод

Decomposition `settings.py` начат с самой изолированной зоны, у которой уже было прямое покрытие. Это снижает риск и позволяет дальше дробить router по bounded helper-группам, а не переписывать его целиком.

## Следующий шаг

- Следующий безопасный кандидат: `Rabota OAuth/token` helper-блок.
- После него можно брать `database cleanup` endpoints или `Google Sheets` refresh/upload path.
