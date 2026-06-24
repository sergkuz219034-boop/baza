# 2026-06-24 Graphify, Runtime Inspector, doctor.py, Job Timeline, Explain Candidate

## Симптом
Дебаг TrafficHub занимал слишком много ручных шагов: нужно было отдельно смотреть контейнеры, health, Redis/job state, PostgreSQL, логи и историю конкретного кандидата.

## Зона системы
Server-first runtime `/root/TrafficHub`: `api/routers/system.py`, `api/routers/jobs.py`, `api/routers/leads.py`, `traffic_hub/services/job_queue.py`, `utils/database.py`, `utils/runtime_store_pg_jobs.py`, `utils/runtime_repository.py`, `tools/doctor.py`, dashboard.

## Гипотеза
Если добавить read-only runtime-инспектор, CLI doctor, persistent timeline job-событий и explain endpoint для лида, первичная диагностика будет занимать 5-15 минут без чтения всего кода.

## Проверка
Подтверждено на live-сервере:
- `/usr/local/bin/python -> /usr/bin/python3` создан, команда `python` доступна.
- `tools/remote_exec.py` пишет uploaded scripts байтами UTF-8 и выводит stdout/stderr как UTF-8.
- `./tools/doctor.py --json` выполняется на сервере.
- `docker compose exec -T autolead_bot ... pytest ...` прошёл: 15 passed.
- `/api/health` вернул `status=ok`.
- commit `74ff3fd8d` запушен в GitHub `sergkuz219034-boop/TrafficHub`.
- commit `70b761e12` добил UI Job Timeline, admin owner-filter и исправил mojibake в серверном README.
- commit `dad9bde3b` перенёс `Инспектор runtime` и `История задач` из `Настройки` в `Admin панель`.

## Наблюдение
`graphify` установлен локально и построил граф по `remote_files`: 1908 nodes, 6055 edges. На сервере `graphify` не установлен; `doctor.py` помечает это как warning, не как critical, потому что Graphify используется как локальная навигационная карта, а не runtime dependency.

## Вывод
Диагностический контур добавлен:
- admin-only `/api/system/runtime-inspector`;
- CLI `tools/doctor.py`;
- persistent `autolead_job_events`;
- owner-scoped `/api/jobs/timeline` с admin owner-filter;
- admin-only UI-блок `История задач`;
- owner-scoped `/api/leads/{lead_id}/explain`.

## Следующий шаг
Если потребуется дальнейшее ускорение разбора кандидатов, подключить `Explain Candidate` в UI рядом с таблицей лидов. Backend endpoint уже есть и owner-scoped.
