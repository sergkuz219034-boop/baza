# PostgreSQL query telemetry

## Когда использовать

Когда нужно понять реальную SQL-нагрузку TrafficHub и не гадать по `seq_scan`.

## Проверить, что telemetry включена

```bash
docker exec -i traffichub_postgres psql -U traffichub -d traffichub -c "SHOW shared_preload_libraries;"
docker exec -i traffichub_postgres psql -U traffichub -d traffichub -c "SELECT extname FROM pg_extension WHERE extname='pg_stat_statements';"
```

Ожидаемо:

- `shared_preload_libraries` содержит `pg_stat_statements`;
- extension `pg_stat_statements` установлен.

## Снять top queries

```bash
docker exec -i traffichub_postgres psql -U traffichub -d traffichub -c "
SELECT
  calls,
  round(total_exec_time::numeric, 2) AS total_ms,
  round(mean_exec_time::numeric, 2) AS mean_ms,
  rows,
  left(regexp_replace(query, '[[:space:]]+', ' ', 'g'), 180) AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;"
```

## Правило интерпретации

Не добавлять индекс только потому, что у таблицы высокий `seq_scan`. Для маленьких таблиц seq scan может быть дешевле индекса. Решение принимается по конкретному запросу, частоте вызовов, времени выполнения и количеству строк.

## Связанные заметки

- [[2026-06-23 TrafficHub full senior audit]]
- [[2026-06-24 PostgreSQL query telemetry]]
- [[Runtime database]]

