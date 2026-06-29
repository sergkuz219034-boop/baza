# 2026-06-29 проверка wiki ошибок и runtime хвостов

## Симптом

- Требование: проверить проект по wiki-ошибкам, инициировать/перепроверить повторяемые сценарии и исправить найденные дефекты.
- Приоритетные зоны из свежих заметок:
  - мигание `Полный цикл: выполняется`;
  - Lovko/Ozon/Onecta `ERR_TIMED_OUT`;
  - Rabota/Zarplata порядок выгрузки и рассылки;
  - нечитаемые статусы/логи;
  - расписание, которое включено без времени запуска.

## Зона системы

- live repo: `/root/TrafficHub`
- commit после исправления: `59512eaf9`
- runtime: `traffichub_app`, `traffichub_worker`, PostgreSQL, Redis
- affected files:
  - `services/leads_service.py`
  - `utils/runtime_repository.py`
  - `api/routers/leads.py`
  - `api/routers/settings_core.py`
  - `docs/leads-excel-import.md`
  - `tests/test_no_mojibake.py`

## Гипотеза

- Основные runtime-ошибки Lovko/spinner уже могли быть исправлены ранее, но в коде и БД могли остаться хвосты, которые возвращают те же симптомы:
  - mojibake в user-facing логах и explain endpoint;
  - stale retry rows после старых timeout;
  - `schedule_enabled=true` при пустом `schedule_times`;
  - битое сохранённое имя листа `Резюме`.

## Проверка

- Проверен live `/api/health`: `status=ok`, `control.backend=postgres`.
- Проверены контейнеры: `traffichub_app`, `traffichub_worker`, `postgres`, `redis`, `account_manager`, `license_*`, `hermes` healthy/running.
- Проверены Docker logs за 24 часа по `ERROR`, `Traceback`, `ERR_TIMED_OUT`, `форма не подтверждена`, `submit не найдена`, `Lovko`, `Ozon`, `Onecta`, `Zarplata`: свежих ошибок не найдено.
- Проверен `autolead_app_log`:
  - текущих error-lines нет;
  - последние Ozon строки у `admin` успешные;
  - найден deploy/restart-хвост `Предыдущий запуск прерван рестартом сервера`.
- Проверен `autolead_retry_queue`:
  - у `alex` оставались 2 старые Ozon timeout rows от 2026-06-27.
- Проверен `control_user_app_configs`:
  - у `artem` и `kursmerkusheva@gmail.com` было mojibake `resume_sheet_name`;
  - у `alex`, `kursmerkusheva@gmail.com`, `sergkuz2190` было `schedule_enabled=true` при пустом `schedule_times`.
- Прогнаны targeted regression tests:
  - `tests/test_dashboard_realtime_spinner.py`
  - `tests/test_runtime_logging.py`
  - `tests/test_vbiv_bot_navigation.py`
  - `tests/test_zarplata_owner_guard.py`
  - `tests/test_leads_service_sheets_flow.py`
  - `tests/test_zarplata_api.py`
  - `tests/test_settings_sheets.py`
  - `tests/test_traffic_tenant_isolation.py`
  - `tests/test_autolead_access.py`
- Результат: `78 passed`.

## Наблюдение

- Runtime сейчас не повторяет свежие Lovko/Ozon/Onecta timeout ошибки.
- Spinner-регрессии покрыты тестами и live-код не содержит старого ticker/repaint контура.
- Реально найденные дефекты были в хвостах:
  - нечитаемые mojibake строки в retry/explain/API/docs;
  - отсутствие общего теста против mojibake в core user-facing файлах;
  - settings-layer позволял сохранять пустое расписание как включённое;
  - в БД были старые битые значения `resume_sheet_name`.

## Исправление

- `services/leads_service.py`: восстановлены русские строки логов retry queue.
- `utils/runtime_repository.py`: восстановлены русские explanation/next_steps для `Explain Candidate`.
- `api/routers/leads.py`: восстановлен `Кандидат не найден`.
- `docs/leads-excel-import.md`: восстановлены `Дата` и тире.
- `api/routers/settings_core.py`: если `schedule_times=[]`, `schedule_enabled` принудительно становится `false`; пустые элементы расписания отбрасываются.
- `tests/test_no_mojibake.py`: добавлен guard против возврата mojibake в core user-facing файлы.
- Runtime data cleanup:
  - `resume_sheet_name` исправлен на `Резюме`;
  - пустые расписания выключены у owners без `schedule_times`.

## Проверка после исправления

- Server tests:
  - `tests/test_no_mojibake.py`
  - `tests/test_settings_core.py`
  - `tests/test_scheduler_config.py`
  - `tests/test_retry_queue_matching.py`
  - `tests/test_dashboard_realtime_spinner.py`
  - `tests/test_runtime_logging.py`
  - `tests/test_vbiv_bot_navigation.py`
  - `tests/test_zarplata_owner_guard.py`
  - `tests/test_leads_service_sheets_flow.py`
  - `tests/test_zarplata_api.py`
  - `tests/test_settings_sheets.py`
  - `tests/test_traffic_tenant_isolation.py`
  - `tests/test_autolead_access.py`
- Результат: `78 passed`.
- In-container smoke after rebuild: `19 passed`.
- `rg` по mojibake markers в исправленных runtime файлах ничего не нашёл.
- Docker image пересобран, `autolead_bot` и `worker` пересозданы.
- Health:
  - `http://127.0.0.1:8080/api/health` — `ok`;
  - `https://traffic-hub.pro/api/health` — `ok`.
- Live containers after deploy: app/worker/postgres/redis/account_manager/license/hermes healthy/running.
- Server repo clean: `main...origin/main`, HEAD `59512eaf9`.

## Ограничение проверки

- `gh` отсутствует на live-host, а GitHub repo private для browser-проверки, поэтому GitHub Actions не были machine-read через CLI.
- Remote HEAD подтверждён через `git ls-remote`: local и remote совпали на `59512eaf91ee3dc7f4c16d8570d4ff4d2ac0833a`.
- Следующее инфраструктурное улучшение: вернуть `gh` на host или добавить проверочный скрипт/контейнер для GitHub checks без зависимости от host PATH.

## Вывод

- Свежие ошибки из wiki по spinner, Lovko timeout и Zarplata order не воспроизвелись на live и покрыты регрессиями.
- Найдены и исправлены два реальных хвоста, которые могли снова выглядеть как “старые ошибки”: mojibake в user-facing текстах и пустое включённое расписание.
- Runtime после deploy работает от commit `59512eaf9`.

## Следующий шаг

- отдельно очистить/обработать stale retry rows `alex` только если владелец включит рабочий form proxy для Lovko/Ozon или явно попросит очистить старую retry queue;
- восстановить machine-read GitHub checks на сервере через `gh` или другой проверочный путь.

