# Runtime database

Теги: #сущность

## Тип

Таблица / модуль БД

## Где находится

`remote_server_snapshot/utils/database.py`

## Роль в системе

Хранит operational state Autolead runtime: owner-scoped `app_log`, кэш лидов, историю отправок, retry queue, run log и остальные runtime данные.

После commit `74ff3fd8d` дополнительно хранит persistent job timeline в таблице `autolead_job_events`. Эта таблица нужна, чтобы расследовать job после refresh/restart API, а не зависеть только от Redis/current-state.

## Входы

- leads service
- settings cleanup endpoints

## Выходы

- runtime state
- статистика job-циклов
- persistent job timeline для `/api/jobs/timeline`

## Зависимости

- [[Leads service]]
- [[Multi-Tenant]]
- [[Job Timeline]]
- [[Runtime Inspector]]

## Типовые сбои или риски

- SQLite bottleneck;
- owner drift при ошибках в user context;
- destructive cleanup endpoints;
- очистка in-memory ленты без очистки persistent `app_log` даёт ложное ощущение успеха.
