# 2026-06-15 Третий decomposition step `api.routers.settings` на `settings_sheets`

## Симптом

После выноса `settings_bundle.py` и `settings_rabota.py` в `api/routers/settings.py` оставался ещё один самостоятельный helper-блок:

- display name для таблиц;
- refresh spreadsheet names через Google Sheets API;
- validation `service_account.json`;
- построение user-scoped пути `service_account__<username>.json`.

Эта логика не должна оставаться смешанной с cleanup endpoints и общим settings patch path.

## Зона системы

- `api/routers/settings.py`
- Google Sheets helper path
- service account upload path

## Гипотеза

Google Sheets/service-account helper-зону можно вынести в отдельный модуль, если:

- сохранить старые endpoint-ы без изменения внешнего поведения;
- вернуть compatibility surface для `_spreadsheet_display_name`;
- не сломать старый monkeypatch-based test path вокруг `_sync_imported_auth_secrets`.

## Проверка

Подтверждено по live source of truth:

- создан `api/routers/settings_sheets.py`;
- из `api/routers/settings.py` вынесены:
  - `spreadsheet_display_name`
  - `refresh_spreadsheet_names`
  - `validate_service_account_upload`
  - `service_account_path`
- добавлен `tests/test_settings_sheets.py`

В процессе проверки обнаружен скрытый совместимый контракт:

- `tests/test_sheets_queues.py` импортирует `_spreadsheet_display_name` из `api.routers.settings`
- `tests/test_settings_import_export.py` monkeypatch-ит `_sync_imported_auth_secrets(files)` как одноаргументный callable

После восстановления compatibility:

- `_spreadsheet_display_name` снова доступен через `api.routers.settings` как alias
- в `settings.py` возвращён wrapper `_sync_imported_auth_secrets(files)`

## Наблюдение

- `api/routers/settings.py` сократился до `791` строк.
- Прямой расширенный settings-suite после синхронизации новых файлов в runtime-container проходит:
  - `tests/test_settings_sheets.py`
  - `tests/test_settings_rabota.py`
  - `tests/test_settings_import_export.py`
  - `tests/test_auth_roles.py`
  - `tests/test_proxy_config.py`
  - `tests/test_sheets_queues.py`
  - итог: `32 passed`

## Вывод

Этот шаг подтвердил два важных факта:

1. `settings.py` действительно режется на bounded helper-зоны без смены endpoint semantics.
2. При decomposition нужно сохранять не только public API, но и внутренние compatibility surfaces, которые уже используются тестами и соседними модулями.

## Следующий шаг

- Следующий безопасный кандидат: `database cleanup` endpoints как отдельная maintenance-зона.
- Отдельно стоит зафиксировать в wiki runtime drift: live source tree и содержимое `/app` в контейнере не полностью совпадают без ручного `docker cp`.
