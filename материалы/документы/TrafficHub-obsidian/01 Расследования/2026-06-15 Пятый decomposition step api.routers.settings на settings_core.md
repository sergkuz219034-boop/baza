# 2026-06-15 Пятый decomposition step `api.routers.settings` на `settings_core`

## Симптом

После выноса `settings_bundle.py`, `settings_rabota.py`, `settings_sheets.py` и `settings_maintenance.py` в `api/routers/settings.py` оставался основной core helper-блок:

- карта editable-полей;
- readonly/read path;
- role-scoped editable subset;
- чтение Rabota auth из control store;
- normalizing proxy URL;
- применение patch к config;
- filter patch data.

Это уже центральная logic-зона router-а, а не отдельная интеграция.

## Зона системы

- `api/routers/settings.py`
- core helper-логика настроек
- editable/readonly/patch path

## Гипотеза

Core helper-зону можно вынести в отдельный модуль, если:

- сохранить старые internal имена через alias/wrapper;
- не сломать существующие тесты, которые импортируют `_normalize_proxy_url` из `api.routers.settings`;
- не сломать read/patch endpoints.

## Проверка

Подтверждено по live source of truth:

- создан `api/routers/settings_core.py`;
- туда вынесены:
  - `EDITABLE`
  - `SUPERJOB_KEYS`
  - `OPERATOR_EDITABLE_KEYS`
  - `ADMIN_ONLY_EDITABLE_KEYS`
  - `read_editable`
  - `read_readonly`
  - `pick_editable`
  - `read_rabota_tokens`
  - `normalize_proxy_url`
  - `apply_editable_patch`
  - `filter_patch_data`

Compatibility сохранена:

- `_normalize_proxy_url` в `settings.py` оставлен как wrapper/alias
- `_apply_editable_patch` в `settings.py` оставлен как wrapper
- route-функции продолжают работать через старые internal имена

Добавлен прямой test coverage:

- `tests/test_settings_core.py`

Проверки:

- `python3 -m compileall -q api/routers/settings_core.py api/routers/settings.py tests/test_settings_core.py`
- после синхронизации новых файлов в runtime-container:
  - `tests/test_settings_core.py`
  - `tests/test_settings_maintenance.py`
  - `tests/test_settings_sheets.py`
  - `tests/test_settings_rabota.py`
  - `tests/test_settings_import_export.py`
  - `tests/test_auth_roles.py`
  - `tests/test_proxy_config.py`
  - `tests/test_sheets_queues.py`
  - итог: `37 passed`

## Наблюдение

- Основной helper-каркас `settings.py` теперь вынесен в отдельный модуль.
- Router-файл после этого шага в основном содержит route-функции, pydantic models и несколько compatibility wrapper-ов.

## Вывод

`api/routers/settings.py` фактически доведён до стадии, где он уже не god-file по helper-логике. Дальнейшие шаги в нём будут либо косметическими, либо затронут уже сами route-группы и admin/license endpoints.

## Следующий шаг

- Либо завершить cleanup `settings.py` и вынести admin/license account routes в отдельный модуль.
- Либо перейти к следующему крупному файлу, если приоритет выше у другого слоя.
