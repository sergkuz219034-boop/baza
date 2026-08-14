# 2026-06-24 закрытие P1-P2 из TrafficHub senior audit

## Симптом

В wiki audit были отмечены P1/P2 ошибки: partner sync crash, `/account-manager/` 500, role drift и model/schema drift.

## Зона системы

- `traffic_hub/api/routers/integrations.py`
- `api/server.py`
- `traffic_hub/authz.py`
- `traffic_hub/models/database.py`
- PostgreSQL `traffichub`

## Гипотеза

P1/P2 можно закрыть точечными правками без переписывания архитектуры: добавить tenant/owner в partner sync, исправить сигнатуру AccountManager redirect, закрепить role-sync тестом и выровнять ORM nullable contract с live DB.

## Проверка

- `tests/test_integrations_sync.py`
- `tests/test_account_manager_proxy_routes.py`
- `tests/test_traffic_authz_role_sync.py`
- `tests/test_tenant_model_constraints.py`
- live smoke `/account-manager/`
- live SQL check `Artem user/user`

## Наблюдение

- Partner sync создавал `PostbackLog` без `tenant_id/owner_username`.
- AccountManager route передавал в helper лишний аргумент.
- `Artem` имел drift `control_license_users=user`, `users=admin`.
- ORM-модели говорили `tenant_id nullable=True`, хотя PostgreSQL уже `NOT NULL`.

## Вывод

P1/P2 из audit закрыты commit `3f42f069b` в `TrafficHub`.

Подтверждение:

- targeted tests: `11 passed`;
- live `/account-manager/`: `302 Location: https://am.traffic-hubcrm.ru/`;
- live role check: `Artem user/user`;
- runtime containers `autolead_server_bot` и `traffichub_worker` healthy.

## Следующий шаг

Дальше не смешивать production bugs с maintenance: отдельно планировать декомпозицию крупных модулей, query-level performance audit, deprecation debt и Redis runtime cleanup.

## Связанные заметки

- [[2026-06-23 TrafficHub full senior audit]]
