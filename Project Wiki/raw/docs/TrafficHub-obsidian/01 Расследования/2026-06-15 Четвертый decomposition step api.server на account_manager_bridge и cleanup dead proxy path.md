# 2026-06-15 Четвертый decomposition step `api.server` на `account_manager_bridge` и cleanup dead proxy path

## Симптом

В `api/server.py` одновременно существовали две модели bridge-пути для `AccountManager`:

- live redirect на публичный `am.*` домен;
- исторический internal proxy path через `httpx`, HTML shell injection и upstream rewrite.

Это создавало ложное впечатление, что live runtime до сих пор зависит от reverse proxy внутри `api/server.py`.

## Зона системы

- `api/server.py`
- bridge между TrafficHub и `AccountManager`
- auth token bootstrap для `am.*`

## Гипотеза

Если live routes `/account-manager*` уже делают только redirect на публичный домен, то internal proxy path является мёртвым кодом и его можно убрать, а живую bridge-часть вынести в отдельный модуль.

## Проверка

Подтверждено на live source of truth `/root/TrafficHub`:

- `account_manager_root` и `account_manager_proxy` routes возвращают `RedirectResponse` на `ACCOUNT_MANAGER_PUBLIC_BASE_URL`;
- `_proxy_account_manager`, `_inject_account_manager_shell`, `_is_account_manager_html_request`, `_account_manager_proxy_target` не вызываются нигде вне собственного внутреннего блока;
- `ACCOUNT_MANAGER_BASE_URL` больше не нужен live path.

После cleanup:

- создан `api/account_manager_bridge.py`;
- в нём оставлены только:
  - `account_manager_access_token`
  - `account_manager_public_target`
- из `api/server.py` удалены:
  - `_proxy_account_manager`
  - `_inject_account_manager_shell`
  - `_is_account_manager_html_request`
  - `_account_manager_proxy_target`
  - `ACCOUNT_MANAGER_BASE_URL`
  - `httpx` import

Проверки:

- `python3 -m compileall -q api/account_manager_bridge.py api/server.py`
- `docker exec autolead_server_bot python -m pytest -q tests/test_account_manager_import.py tests/test_traffic_auth_external.py tests/test_autolead_access.py`

## Наблюдение

- `api/server.py` сократился до `1315` строк.
- Внутри entrypoint больше нет мёртвого proxy/shell injection path для `AccountManager`.
- Документация теперь должна описывать только реальный live bridge: redirect + token bootstrap.

## Вывод

Это не просто ещё один split helper-кода, а устранение расхождения между кодовой базой и фактическим runtime-поведением.

`AccountManager` на текущем live контуре подключён как отдельное приложение через публичный домен, а не как embedded reverse proxy внутри `TrafficHub`.

## Следующий шаг

- Следующий кандидат на decomposition: register/license helper path или `api/routers/settings.py`.
- По приоритету безопаснее начать с fragmentation `api/routers/settings.py`, потому что `services/leads_service.py` остаётся самым рискованным god-file.
