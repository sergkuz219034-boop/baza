# Monitoring

Теги: #архитектура

## Что подтверждено

- file logging в `main.py` и `AccountManager/api/main.py`
- healthcheck в `docker-compose.yml` для всех трёх приложений
- request logging в AccountManager
- job status endpoint `/status`
- websocket broadcast статусов job
- у `AccountManager` есть фоновый scheduler для периодических проверок Google / Telegram / Social accounts

## На что опирается операционное наблюдение

- `autolead.log`
- `account_manager.log`
- health endpoints
- runtime таблицы `run_log`, `retry_queue`

## Чего не хватает в snapshot

- нет подтверждения внешней метрик-системы;
- нет подтверждения централизованного лог-агрегатора;
- нет подтверждения tracing.

## Смежные страницы

- [[Performance]]
- [[Debugging]]
