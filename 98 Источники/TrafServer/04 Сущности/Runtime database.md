# Runtime database

Теги: #сущность

## Тип

Таблица / модуль БД

## Где находится

`remote_server_snapshot/utils/database.py`

## Роль в системе

Хранит operational state Autolead runtime: owner-scoped `app_log`, кэш лидов, историю отправок, retry queue, run log и остальные runtime данные.

## Входы

- leads service
- settings cleanup endpoints

## Выходы

- runtime state
- статистика job-циклов

## Зависимости

- [[Leads service]]
- [[Multi-Tenant]]

## Типовые сбои или риски

- SQLite bottleneck;
- owner drift при ошибках в user context;
- destructive cleanup endpoints;
- очистка in-memory ленты без очистки persistent `app_log` даёт ложное ощущение успеха.
