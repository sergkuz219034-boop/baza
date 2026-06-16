# 2026-06-15 Второй decomposition step `api.server` на `dashboard_assets`

## Симптом

После первого выноса `dashboard_log_history` файл `api/server.py` всё ещё держал смешанный технический helper-блок для dashboard shell:

- no-cache headers;
- расчёт asset version по mtime;
- чтение HTML;
- render `dashboard/index.html`.

Этот код не относится к auth, jobs, WebSocket или Account Manager proxy, но продолжал жить внутри общего entrypoint.

## Зона системы

- `api/server.py`
- dashboard/static entry helpers
- HTML shell render path

## Гипотеза

Блок dashboard/static helper-ов можно безопасно вынести в отдельный модуль без изменения runtime-поведения, если:

- сохранить старые internal helper-имена через import alias;
- не трогать маршруты;
- не менять `DASHBOARD_DIR` и существующий `StaticFiles` flow.

## Проверка

Подтверждено на live source of truth `/root/TrafficHub`:

- создан `api/dashboard_assets.py`;
- из `api/server.py` вынесены:
  - `no_cache_headers`
  - `dashboard_asset_version`
  - `read_html`
  - `render_dashboard_index`
- `api/server.py` продолжает использовать их через alias:
  - `_no_cache_headers`
  - `_dashboard_asset_version`
  - `_read_html`
  - `_render_dashboard_index`

Проверки:

- `python3 -m compileall -q api/dashboard_assets.py api/dashboard_log_history.py api/server.py`
- `docker exec autolead_server_bot python -m pytest -q tests/test_log_history.py`
- `docker exec autolead_server_bot python -m pytest -q tests/test_account_manager_import.py tests/test_autolead_access.py`

## Наблюдение

- `api/server.py` сократился до `1548` строк.
- `api/dashboard_assets.py` содержит `36` строк и изолирует purely infrastructural dashboard helper-логику.
- Auth/session rate limit, register/login flow и Account Manager proxy пока остаются внутри `api/server.py`.

## Вывод

`api/server.py` начал разбираться не по абстрактным слоям, а по реально изолируемым техническим зонам. Это снижает размер entrypoint и делает следующий split менее рискованным.

## Следующий шаг

- Следующий кандидат на безопасный вынос: auth/session helper-блок (`_origin_from_url`, `_allowed_origins`, `_session_https_only`, login rate limit helpers).
- Альтернативный кандидат: Account Manager proxy helper-блок, но он рискованнее из-за `httpx`/redirect/injection path.
