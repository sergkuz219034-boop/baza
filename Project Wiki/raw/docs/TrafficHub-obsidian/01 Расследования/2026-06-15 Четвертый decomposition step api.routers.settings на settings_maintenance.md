# 2026-06-15 Четвертый decomposition step `api.routers.settings` на `settings_maintenance`

## Симптом

После выноса `settings_bundle.py`, `settings_rabota.py` и `settings_sheets.py` внутри `api/routers/settings.py` оставался отдельный maintenance-блок:

- owner-scoped очистка локальной БД;
- очистка `autofit_seen`, `leads`, `send_history`, `invite_history`, `retry_queue`, `run_log`;
- удаление debug-файлов.

Этот блок не относится ни к settings patch path, ни к OAuth, ни к Google Sheets.

## Зона системы

- `api/routers/settings.py`
- maintenance / cleanup endpoints
- debug artifact cleanup

## Гипотеза

Maintenance-зону можно вынести как отдельный router-модуль и подключить назад через `router.include_router(...)`, не меняя внешние endpoint paths.

## Проверка

Подтверждено по live source of truth:

- создан `api/routers/settings_maintenance.py`;
- в нём вынесены:
  - `/db`
  - `/db/autofit`
  - `/db/leads`
  - `/db/send-history`
  - `/db/invite-history`
  - `/db/screenshots`
  - `/db/retry-queue`
  - `/db/run-log`
- helper `clear_debug_artifacts(base_dir)` вынесен в тот же модуль
- `api/routers/settings.py` теперь подключает `maintenance_router`

Добавлен прямой test coverage:

- `tests/test_settings_maintenance.py`

Проверки:

- `python3 -m compileall -q api/routers/settings_maintenance.py api/routers/settings.py tests/test_settings_maintenance.py`
- после синхронизации новых файлов в runtime-container:
  - `tests/test_settings_maintenance.py`
  - `tests/test_settings_sheets.py`
  - `tests/test_settings_rabota.py`
  - `tests/test_settings_import_export.py`
  - `tests/test_auth_roles.py`
  - `tests/test_proxy_config.py`
  - `tests/test_sheets_queues.py`
  - итог: `34 passed`

## Наблюдение

- `settings.py` продолжает уменьшаться по реально отделимым bounded зонам.
- Maintenance-блок удалось вынести без дополнительных compatibility hotfix, кроме уже существующего контейнерного `docker cp` шага для новых файлов.

## Вывод

`api/routers/settings.py` уже больше не является единым “мешком” из import/export, OAuth, Google Sheets и maintenance. Разделение стало соответствовать фактическим зонам ответственности.

## Следующий шаг

- Следующий кандидат: общий settings patch/read path (`editable`, `readonly`, role-scoped patch logic).
- Альтернатива: перейти к следующему крупному файлу, если выгоднее не дробить `settings.py` дальше в этом цикле.
