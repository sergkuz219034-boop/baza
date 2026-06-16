# 2026-06-15 Шестой decomposition step `api.routers.settings` на `settings_license_accounts`

## Симптом

После выноса helper-слоёв в `api/routers/settings.py` оставался отдельный admin-only блок:

- `GET /license-accounts`
- `PATCH /license-accounts/{login}/role`
- `PATCH /license-accounts/{login}`
- `DELETE /license-accounts/{login}`

Этот блок не относится к owner-scoped patch/import/upload path и держал в роутере отдельную административную ответственность.

## Зона системы

- `api/routers/settings.py`
- admin/license account endpoints
- `utils.license`

## Гипотеза

Admin-only `license account` routes можно вынести в отдельный subrouter без изменения поведения, если:

- сохранить тот же URL-space через `include_router`;
- не трогать patch/import/upload ветки;
- подтвердить поведение в runtime-container, а не только по исходникам.

## Проверка

Подтверждено по live source of truth:

- создан `api/routers/settings_license_accounts.py`;
- туда вынесены:
  - `get_license_accounts`
  - `patch_license_account_role`
  - `update_license_account`
  - `delete_license_account`
  - `RolePatch`
  - `LicensePatch`
- `api/routers/settings.py` теперь только подключает `license_accounts_router` через `router.include_router(...)`.

Добавлен прямой test coverage:

- `tests/test_settings_license_accounts.py`

Проверки:

- `python3 -m compileall -q api/routers/settings.py api/routers/settings_license_accounts.py tests/test_settings_license_accounts.py`
- после `docker cp` новых файлов в `autolead_server_bot`:
  - `tests/test_settings_license_accounts.py`
  - `tests/test_settings_core.py`
  - `tests/test_settings_maintenance.py`
  - `tests/test_settings_sheets.py`
  - `tests/test_settings_rabota.py`
  - `tests/test_settings_import_export.py`
  - `tests/test_auth_roles.py`
  - `tests/test_proxy_config.py`
  - `tests/test_sheets_queues.py`
  - итог: `41 passed`

## Наблюдение

- `api/routers/settings.py` сократился до `487` строк.
- Route-space `/api/settings/license-accounts*` не менялся.
- Разделение ответственности стало чище:
  - `settings.py` держит owner-scoped settings flow;
  - `settings_license_accounts.py` держит admin-only учётные записи.

## Вывод

`api/routers/settings.py` перестал смешивать пользовательские runtime-настройки и административное управление аккаунтами в одном файле. Это не меняет live API, но снижает когнитивную нагрузку при дебаге прав доступа и admin-panel сценариев.

## Следующий шаг

- Либо вынести оставшиеся route-группы `settings.py` по доменам, если это даст реальный выигрыш.
- Либо перейти к следующему крупному файлу, потому что helper/admin split в `settings.py` уже доведён до разумной границы.
