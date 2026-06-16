# 2026-06-17 Live product DB backend for stats_service

## Симптом

После разбора `P2` оставался открытый вопрос:

- является ли SQLite path в `services/stats_service.py` реально активным на live-хосте;
- или это уже только compatibility branch, которая не участвует в production metrics path.

## Зона системы

- live repo `/root/TrafficHub`
- контейнер `autolead_server_bot`
- `traffic_hub.config.settings`
- `services/stats_service.py`

## Гипотеза

Если live `traffic_hub` product DB уже работает через PostgreSQL, то:

- `services/stats_service.py:_traffic_db_path()` должен возвращать `None`;
- SQLite path для postback-метрик не должен быть активным production path;
- это будет не active runtime issue, а documented metrics gap/compatibility branch.

## Проверка

На live-хосте подтверждено:

- `docker compose ps` показывает healthy product contour:
  - `autolead_server_bot`
  - `traffichub_worker`
  - `traffichub_postgres`
  - `traffichub_redis`
  - связанные license/account_manager/caddy сервисы
- внутри контейнера `autolead_bot`:
  - `traffic_hub.config.settings.database_url = postgresql+asyncpg://traffichub:traffichub@postgres:5432/traffichub`
  - `services.stats_service._traffic_db_path() = None`
  - SQLite file path для product DB не резолвится

## Наблюдение

- live `traffic_hub` product DB уже не SQLite;
- SQLite branch в `services/stats_service.py` сейчас не является активным production path;
- при текущем live backend функция `get_postback_metrics()` не переключается в PostgreSQL-aware branch, а деградирует в пустые метрики, если SQLite path отсутствует.

## Вывод

На `2026-06-17` SQLite-ветку `services/stats_service.py` надо трактовать так:

- это не доказательство SQLite-first runtime;
- это не active product DB path на live;
- это compatibility/legacy branch и одновременно потенциальный metrics gap, если postback-метрики ожидаются из PostgreSQL product DB.

## Следующий шаг

1. Поднять это в краткий эксплуатационный канон.
2. Отделить в документации:
   - active `Autolead runtime`
   - active `traffic_hub` product DB
   - legacy SQLite metrics branch в `stats_service.py`
3. При необходимости отдельным инженерным stream проверить, нужен ли PostgreSQL-aware path для `postback_logs` и `conversions`.
