# Performance

Теги: #архитектура

## Подтверждённые приёмы

- SQLite работает в `WAL`;
- runtime избегает параллельного запуска полного цикла через `_cycle_running`;
- config caching с TTL уменьшает лишние чтения;
- owner-scoped индексы добавлены в runtime и TrafficHub миграциях;
- websocket использует user-scoped broadcast вместо общего fanout.

## Ограничения

- SQLite остаётся узким местом при росте нагрузки;
- часть операций всё ещё синхронна и потоковая;
- retry/scrape/send живут в одном приложении и конкурируют за shared runtime.

## Смежные страницы

- [[Database]]
- [[Monitoring]]
