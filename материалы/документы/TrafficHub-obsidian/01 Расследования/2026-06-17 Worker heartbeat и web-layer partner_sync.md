# 2026-06-17 Worker heartbeat и web-layer partner_sync

## Симптом

- в канонической wiki были только общие формулировки про worker heartbeat и hourly `partner_sync`;
- не было короткой подтверждённой фиксации, где именно это живёт в live-коде и runtime.

## Зона системы

- worker execution
- web lifecycle loops
- docker healthcheck

## Гипотеза

- worker heartbeat пишется самим `traffic_hub/worker.py` в файловый runtime artefact;
- `partner_sync` живёт не в worker, а в web-layer `api/server.py` и запускается через lifespan loop;
- worker health на live считается по свежести heartbeat файла, а не по отдельному HTTP endpoint.

## Проверка

- просмотрен live source tree `/root/TrafficHub`:
  - `traffic_hub/worker.py`
  - `api/server.py`
  - `docker-compose.yml`
- проверен live runtime:
  - `docker exec traffichub_worker sh -lc 'date +%s; cat /app/data/runtime/worker.heartbeat'`
  - `docker logs --since 2h autolead_server_bot | grep partner_sync`

## Наблюдение

- `traffic_hub/worker.py`:
  - `_HEARTBEAT_FILE = Path(os.environ.get('WORKER_HEARTBEAT_FILE', '/app/data/runtime/worker.heartbeat'))`
  - `_write_heartbeat(state)` пишет строку вида `state:iso_ts`
  - `run_worker()` пишет heartbeat на `starting`, затем в основном loop и на `stopped`
  - `WORKER_MAX_PARALLEL_OWNERS` читается из env и логируется при старте worker.
- `docker-compose.yml`:
  - web и worker получают `WORKER_HEARTBEAT_FILE=/app/data/runtime/worker.heartbeat`
  - worker получает `WORKER_MAX_PARALLEL_OWNERS=${WORKER_MAX_PARALLEL_OWNERS:-2}`
  - healthcheck worker требует, чтобы heartbeat файл существовал и был моложе `180` секунд.
- `api/server.py`:
  - `_run_partner_sync_cycle()` логирует старт sync и проходит пользователей с network integrations;
  - `_partner_sync_loop()` крутит цикл с `await asyncio.sleep(_AUTO_SYNC_INTERVAL_SEC)`;
  - в lifespan создаётся `partner_sync_task = asyncio.create_task(_partner_sync_loop())`.
- live runtime на `2026-06-17`:
  - heartbeat файл содержал `alive:2026-06-16T22:30:32.179989+00:00`;
  - web log за последние 2 часа показал hourly:
    - `2026-06-17 00:27:33 [partner_sync] INFO: TrafficHub: sync for user audit-admin`
    - `2026-06-17 01:27:33 [partner_sync] INFO: TrafficHub: sync for user audit-admin`

## Вывод

- `partner_sync` — это web-layer lifecycle loop, а не worker-задача;
- worker liveliness на production host завязана на heartbeat file, который пишет `traffic_hub/worker.py`;
- safe operational assumptions:
  - свежий heartbeat нужен как признак живого worker;
  - hourly `partner_sync` надо искать в логах `autolead_server_bot`, а не `traffichub_worker`.

## Следующий шаг

- обновить канонические страницы `[[05_Эксплуатация/Воркеры и расписание]]`, `[[04_Код/Бэкенд]]`, `[[05_Эксплуатация/Мониторинг и алерты]]` и `[[06_Отладка/Рецепт отладки]]`;
- при следующем инциденте по scheduler отдельно различать web-loop `partner_sync` и worker queue path.
