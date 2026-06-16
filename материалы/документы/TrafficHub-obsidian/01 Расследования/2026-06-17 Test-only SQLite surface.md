# 2026-06-17 Test-only SQLite surface

## Симптом

После разбора `P1`, `P2` и `P3` оставалась последняя зона SQLite-хвоста:

- тесты и fixture-пути, которые активно используют SQLite;
- не было ясно, где это нормальная unit/integration-изоляция, а где такой выбор может вводить в заблуждение насчёт live storage contract.

## Зона системы

- live repo `/root/TrafficHub`
- `tests/test_database.py`
- `tests/test_leads_router.py`
- `tests/test_traffic_hub_migrations.py`
- `tests/test_integrations_sync.py`
- `tests/test_traffic_auth_external.py`
- `tests/test_traffic_tenant_isolation.py`
- `tests/test_account_manager_import.py`

## Гипотеза

SQLite в тестах на `2026-06-17` используется в основном по четырём причинам:

1. быстрый isolated fixture для legacy/runtime storage unit-тестов;
2. дешёвый DB backend для tenant/auth/integration сценариев `traffic_hub`;
3. миграционные regression-тесты на legacy SQLite schema;
4. local router/debug tests, которые напрямую проверяют SQLite-oriented code paths.

## Проверка

По live-коду подтверждено:

- `tests/test_database.py` напрямую тестирует `utils/database.py` как SQLite-oriented storage facade;
- `tests/test_leads_router.py` импортирует `sqlite3` и вручную пишет в `test_db.DB_PATH` для проверки owner-scope и router filtering;
- `tests/test_traffic_hub_migrations.py` строит временные `sqlite:///...` и `sqlite+aiosqlite:///...` БД для проверки legacy schema repair и migration behaviour;
- `tests/test_integrations_sync.py`, `tests/test_traffic_auth_external.py`, `tests/test_traffic_tenant_isolation.py` используют временные SQLite engines как изолированную test DB для app-level сценариев;
- `tests/test_account_manager_import.py` передаёт SQLite `DB_PATH` в env для import-сценариев.

## Наблюдение

### Нормальная test-only роль

- SQLite здесь дешёвый временный backend;
- он ускоряет тесты и минимизирует внешние зависимости;
- для migration regression и tenant isolation это понятный инструментальный выбор.

### Где есть риск ложной интерпретации

- `tests/test_database.py` и `tests/test_leads_router.py` ближе всего к legacy/runtime SQLite mental model;
- если читать их без контекста live system, можно ошибочно решить, что runtime contract всё ещё SQLite-centric;
- множество `sqlite+aiosqlite` tests в `traffic_hub` слое доказывают test strategy, но не доказывают текущий production backend.

### Что это не означает

- не означает, что `Autolead runtime` live-path всё ещё SQLite-first;
- не означает, что `traffic_hub` product DB live-path всё ещё SQLite;
- не означает, что `control_store` active backend живёт в `control.db`.

## Вывод

На `2026-06-17` test-only SQLite surface надо описывать так:

- это в основном fixture/integration convenience layer;
- production-risk у него низкий;
- риск находится в неверной интерпретации: тестовые SQLite backend'ы нельзя использовать как source of truth о live storage contract.

## Следующий шаг

1. Поднять эту роль в краткий testing/debug канон.
2. Явно отделить test fixtures от live runtime evidence.
3. Если когда-нибудь чистить SQLite дальше, тестовый слой рассматривать отдельно от production cleanup stream.
