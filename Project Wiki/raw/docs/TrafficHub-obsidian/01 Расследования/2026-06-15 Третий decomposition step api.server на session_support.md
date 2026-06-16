# 2026-06-15 Третий decomposition step `api.server` на `session_support`

## Симптом

После выноса dashboard log/history и dashboard/static helper-ов в `api/server.py` оставался ещё один технический блок, не относящийся к бизнес-роутам:

- нормализация origin;
- CORS allowlist;
- secure-cookie flag;
- login rate limit по IP;
- сборка session payload.

Этот код продолжал смешиваться с route-entrypoint, хотя по сути обслуживает только auth/session plumbing.

## Зона системы

- `api/server.py`
- dashboard auth/session flow
- cookie/CORS/rate-limit helper-логика

## Гипотеза

Если вынести auth/session helper-ы в отдельный модуль и сохранить старые internal helper-имена через import alias, можно уменьшить `api/server.py` без изменения login semantics.

## Проверка

Подтверждено на live source of truth `/root/TrafficHub`:

- создан `api/session_support.py`;
- из `api/server.py` вынесены:
  - `origin_from_url`
  - `allowed_origins`
  - `session_https_only`
  - `request_ip`
  - `login_is_rate_limited`
  - `record_failed_login`
  - `clear_failed_logins`
  - `session_payload`

`api/server.py` продолжает использовать их через alias:

- `_origin_from_url`
- `_allowed_origins`
- `_session_https_only`
- `_request_ip`
- `_login_is_rate_limited`
- `_record_failed_login`
- `_clear_failed_logins`
- `_session_payload`

Проверки:

- `python3 -m compileall -q api/session_support.py api/dashboard_assets.py api/dashboard_log_history.py api/server.py`
- `docker exec autolead_server_bot python -m pytest -q tests/test_traffic_auth_external.py tests/test_account_manager_import.py tests/test_access.py tests/test_autolead_access.py`

## Наблюдение

- `api/server.py` сократился до `1487` строк.
- `api/session_support.py` содержит `76` строк.
- Login/session path остаётся покрыт container smoke тестами, а не только compile check.

## Вывод

В `api/server.py` уже отделены три технические зоны:

- `dashboard_log_history`
- `dashboard_assets`
- `session_support`

Это подтверждает, что decomposition идёт по реальным внутренним bounded helper-зонам, а не по формальному «переписыванию ради архитектуры».

## Следующий шаг

- Следующий кандидат: `Account Manager` proxy/shell injection path.
- Он рискованнее, потому что затрагивает `httpx`, redirect rewriting и HTML shell injection, поэтому его нужно брать отдельно и только с дополнительным smoke.
