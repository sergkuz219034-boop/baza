# 2026-06-15 Второй decomposition step `api.routers.settings` на `settings_rabota`

## Симптом

После выноса `settings_bundle.py` в `api/routers/settings.py` оставался отдельный helper-блок, связанный только с Rabota OAuth/token flow:

- чтение proxy URL;
- сборка `requests` proxy dict;
- подпись payload;
- чтение server time;
- redirect URI fallback.

Этот код не относится к общему settings patch path и не должен оставаться смешанным с import/export, cleanup и upload endpoint-ами.

## Зона системы

- `api/routers/settings.py`
- Rabota OAuth/token helpers
- proxy/signature/time/redirect path

## Гипотеза

Rabota helper-логика может быть вынесена в отдельный модуль без смены endpoint-поведения, а её ключевые части можно закрыть прямым unit test набором.

## Проверка

Подтверждено на live source of truth `/root/TrafficHub`:

- создан `api/routers/settings_rabota.py`;
- из `api/routers/settings.py` вынесены:
  - `rabota_proxy_url`
  - `rabota_request_proxies`
  - `make_signature`
  - `get_server_time`
  - `default_redirect_uri`

Дополнительно добавлен прямой test coverage:

- `tests/test_settings_rabota.py`

Проверки:

- `python3 -m compileall -q api/routers/settings_rabota.py api/routers/settings.py tests/test_settings_rabota.py`
- host-level `python3 -m pytest -q tests/test_settings_rabota.py`
- container-smoke `tests/test_settings_import_export.py tests/test_auth_roles.py tests/test_proxy_config.py tests/test_sheets_queues.py`

## Наблюдение

- `api/routers/settings.py` сократился до `865` строк.
- `api/routers/settings_rabota.py` содержит `54` строки.
- Новый test-файл присутствует в live source tree, но не виден внутри уже работающего контейнера `/app`.

## Вывод

Decomposition `settings.py` продолжается по bounded helper-зонам и теперь покрывает уже две независимые технические области:

- import/export bundle
- Rabota OAuth/token helpers

Отдельно подтверждено расхождение между live source tree и текущим содержимым контейнера `/app`: новые host-файлы не всегда сразу доступны в контейнерном test path.

## Следующий шаг

- Следующий безопасный кандидат: `Google Sheets` helper-блок (`refresh spreadsheet names`, service account upload support).
- Альтернативный кандидат: `database cleanup` endpoints как отдельная maintenance-зона.
