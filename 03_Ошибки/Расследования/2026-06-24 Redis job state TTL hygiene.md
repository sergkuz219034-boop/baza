# 2026-06-24 Redis job state TTL hygiene

## Симптом

В senior audit Redis содержал старые `traffic_hub:jobs:progress:*` и `traffic_hub:jobs:state:*` ключи для debug/test owners. Такие ключи жили без TTL и могли создавать ложное впечатление, что у пользователя есть старое runtime-состояние.

## Зона системы

- `utils/state.py`
- `traffic_hub/services/job_queue.py`
- Redis `traffic_hub:jobs:*`
- контейнеры `autolead_server_bot`, `traffichub_worker`, `traffichub_redis`

## Гипотеза

Проблема не в PostgreSQL и не в UI, а в том, что Redis progress/state keys создавались без срока жизни. После рестартов и тестовых запусков они оставались в runtime бесконечно.

## Проверка

- Live Redis показал `ttl=-1` для `traffic_hub:jobs:progress:*` и `traffic_hub:jobs:state:*`.
- В `utils/state.py` `request_stop()`, `reset_progress()` и `update_progress()` писали ключи без `ex/expire`.
- В `traffic_hub/services/job_queue.py::_write_state()` состояние job писалось через `client.set(...)` без TTL.

## Наблюдение

На сервере были найдены stale keys для `debug-worker-*`, `test-vbiv-owner`, `debuglogs`, `artem2`, `artemka`. Реальные пользовательские ключи (`artem`, `admin`, `alex`, `user`, `sergkuz2190`) были оставлены, но получили TTL 7 дней.

## Вывод

Redis job state должен быть runtime-кэшем, а не постоянным хранилищем. Каноничные данные лежат в PostgreSQL, поэтому progress/state/stop keys обязаны иметь TTL.

## Следующий шаг

Оставшиеся P2/P3 пункты из senior audit закрывать отдельно: `pg_stat_statements` для query-level SQL telemetry и dependency warning pass.

## Подтверждение

- Commit TrafficHub: `e4818e56a Fix Redis job state TTL hygiene`.
- Тесты: `tests/test_state.py`, `tests/test_job_queue_transition.py`.
- Runtime smoke: `GET http://127.0.0.1:8080/api/health` внутри `autolead_server_bot` вернул `status=ok`.
- Live cleanup: stale debug/test Redis keys удалены; реальные user keys получили TTL `604800`.

