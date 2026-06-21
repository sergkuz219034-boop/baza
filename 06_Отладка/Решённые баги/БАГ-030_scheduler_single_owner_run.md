# БАГ-030: плановый full-cycle ставился в очередь только для одного owner

## Симптом

По формулировке release-задачи полный цикл должен отрабатывать не только для `admin`, а для всех реально доступных пользователей с рабочим owner-scoped контуром. Фактический scheduler-path ставил `run` только для одного `owner`.

## Зона системы

- `services/leads_service.py`
- `traffic_hub/services/job_queue.py`
- `utils/control_store.py`
- PostgreSQL таблицы `control_license_users`, `control_user_app_configs`, `control_user_app_auth`

## Гипотеза

Если `run_server_mode()` при срабатывании расписания использует только `scheduler_owner` / `_resolve_autolead_owner()`, то плановый full-cycle охватывает один профиль и не fan-out'ится по остальным активным пользователям, даже если у них есть отдельные конфиги и auth.

## Проверка

- В live repo `/root/TrafficHub` на `2026-06-21` `services/leads_service.py::run_server_mode()` до правки вызывал `job_queue.enqueue_job(owner, "run", ...)` ровно один раз.
- Runtime-факт из PostgreSQL:
  - в `control_license_users` есть 6 активных логинов: `admin`, `Artem`, `alex`, `alice`, `kursmerkusheva@gmail.com`, `sergkuz2190`;
  - owner-scoped auth есть не у всех, но минимум у `admin`, `artem`, `alex`, `kursmerkusheva@gmail.com` есть и config, и auth.
- Новая логика добавила `_iter_schedulable_owners()`:
  - берёт только активных пользователей из `control_store.list_users()`;
  - требует существующий user-config;
  - требует существующий user-auth;
  - повторно проверяет, что effective config даёт активный runtime-контур через `rabota_ru`, `offer_mapping` или `google_sheets.enabled`.
- Временный одноразовый контейнер на образе `traffichub-autolead_bot` прогнал тесты уже по host repo `/root/TrafficHub`:
  - `tests/test_scheduler_config.py`
  - `tests/test_worker_parallel.py`
  - `tests/test_jobs_router.py`
  - `tests/test_ws_manager.py`
  - `tests/test_leads_service_sheets_flow.py`
  - `tests/test_sheets_queues.py`
  - `tests/test_vbiv_offer_matching.py`
  - результат: `48 passed`.

## Наблюдение

Проблема была не в worker parallelism и не в owner-locks. `traffic_hub/worker.py` уже умеет subprocess-per-owner и ограничение `WORKER_MAX_PARALLEL_OWNERS`; дефект находился раньше, на scheduler enqueue boundary.

После правки один scheduler tick может поставить несколько owner-scoped `run` jobs, а busy owner'ы логируются отдельно и не блокируют остальных.

## Вывод

Это был общий scheduler fan-out bug. До правки автоматический full-cycle не масштабировался на всех активных пользователей, даже если worker-контур умел параллельное owner-scoped исполнение.

## Следующий шаг

1. После deploy проверить live-лог планировщика: в одном тике должны появляться несколько `owner:period`, а не один `admin`.
2. Если у пользователя есть config, но нет auth, это теперь осознанно `skip`, а не скрытый нерабочий запуск.
3. Если потребуется разные `schedule_times` для разных пользователей, это отдельное архитектурное ограничение текущего scheduler design, а не часть этого фикса.
