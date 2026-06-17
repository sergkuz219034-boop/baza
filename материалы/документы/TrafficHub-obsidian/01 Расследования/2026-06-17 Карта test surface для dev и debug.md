# 2026-06-17 Карта test surface для dev и debug

## Симптом

- канонический раздел `[[08_Тестирование]]` был слишком коротким и не отражал, какие регрессии реально покрываются test suite.

## Зона системы

- automated tests
- regression surface
- debug workflow

## Гипотеза

- текущий `tests/*` уже покрывает ключевые зоны для dev/debug:
  - worker parallelism
  - websocket manager
  - tenant isolation
  - external/local auth
  - integrations sync
  - runtime log filtering
  - backup/import backup logic

## Проверка

- просмотрен live test tree `/root/TrafficHub/tests`
- отдельно проверены:
  - `tests/test_worker_parallel.py`
  - `tests/test_ws_manager.py`
  - `tests/test_traffic_tenant_isolation.py`
  - `tests/test_integrations_sync.py`
  - `tests/test_traffic_auth_external.py`
  - `tests/test_runtime_logging.py`
  - `tests/test_system_backups.py`
  - `tests/test_settings_import_export.py`
  - `tests/test_offers_import_export.py`

## Наблюдение

- `test_worker_parallel.py`:
  - проверяет multi-owner spawn
  - проверяет соблюдение `WORKER_MAX_PARALLEL_OWNERS`
  - проверяет targeted stop только для нужного owner
- `test_ws_manager.py`:
  - проверяет recent log history snapshot
  - проверяет explicit snapshot
  - проверяет owner-scoped status delivery
- `test_traffic_tenant_isolation.py`:
  - проверяет owner-scope на offers, leads, messengers, funnels, finance
  - проверяет создание новых сущностей с правильным `owner_username`
- `test_integrations_sync.py`:
  - проверяет нормализацию raw rows
  - проверяет импорт conversions/financial/postback/lead state
  - проверяет user-owned integration credentials
- `test_traffic_auth_external.py`:
  - проверяет external auth mode
  - проверяет bootstrap через bearer token
  - проверяет local cookie auth login/bootstrap/logout
- `test_runtime_logging.py`:
  - проверяет фильтрацию технического шума
  - проверяет, какие строки считаются UI-relevant
- backup/import backup tests:
  - `test_system_backups.py`
  - `test_settings_import_export.py`
  - `test_offers_import_export.py`

## Вывод

- test suite уже является рабочей картой регрессий для dev/debug, а не только “папкой tests”;
- при расследовании бага полезно сначала определить, есть ли уже точечный test surface в одной из подтверждённых зон, и только потом писать новый тест;
- использование SQLite в этих тестах — в основном isolated fixture path, а не доказательство live backend choice.

## Следующий шаг

- обновить `[[08_Тестирование/Стратегия]]`, `[[08_Тестирование/Тестовые сценарии]]`, `[[08_Тестирование/Тестовые данные]]`, `[[06_Отладка/Инциденты]]`, `[[06_Отладка/Постмортемы]]`;
- при новых регрессиях сначала помечать, какой existing test surface уже должен был бы их поймать.
