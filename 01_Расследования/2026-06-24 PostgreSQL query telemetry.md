# 2026-06-24 PostgreSQL query telemetry

## Симптом

Senior audit показывал высокие `seq_scan` на нескольких таблицах, но table-level статистика не отвечала на главный вопрос: какие именно запросы создают нагрузку.

## Зона системы

- `docker-compose.yml`
- PostgreSQL `traffichub`
- extension `pg_stat_statements`

## Гипотеза

Оптимизировать индексы по одному `pg_stat_user_tables.seq_scan` нельзя: часть таблиц маленькая (`users`, `control_*`), и seq scan может быть нормальным планом. Нужна query-level telemetry.

## Проверка

- До исправления: `SHOW shared_preload_libraries` возвращал пустое значение, extension `pg_stat_statements` не был установлен.
- После исправления: `shared_preload_libraries=pg_stat_statements`, extension создан в live DB.
- `docker compose config --quiet` прошёл.
- После рестарта `autolead_server_bot` вернул `/api/health status=ok`.

## Наблюдение

Первичная выборка `pg_stat_statements` после рестарта содержит в основном startup/init queries. Это ожидаемо: статистика включена только сейчас, и для выводов по hot SQL нужно дождаться реальной нагрузки.

## Вывод

Шаг "добавить query-level evidence" закрыт. Следующие SQL-оптимизации должны ссылаться на `pg_stat_statements`, а не на догадки по table-level counters.

## Следующий шаг

После нескольких рабочих циклов снять top queries по `total_exec_time`, `mean_exec_time`, `calls`, `rows`, затем отдельно решать, нужен индекс, переписывание запроса или снижение polling.

## Подтверждение

- Commit TrafficHub: `631f14506 Enable PostgreSQL query telemetry`.
- Live DB: `SHOW shared_preload_libraries` -> `pg_stat_statements`.
- Live DB: `SELECT extname FROM pg_extension WHERE extname='pg_stat_statements'` -> `pg_stat_statements`.

