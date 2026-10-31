# Redis job state

## Идемпотентный учёт RU source outcome — проверено 2026-10-18, 23:40 МСК

Origin commit `53cba5b4b` принимает случайный `event_id` RU запроса `/source-outcome`. `services/source_control.py` под существующим owner policy lock кэширует результат на 6 часов по owner/source/event, поэтому повтор того же события не увеличивает трёхошибочный счётчик и не выключает источник снова. `traffic_hub/remote_worker.py` повторяет transient запросы `/source-allowed` (только чтение) и `/source-outcome` (с тем же event ID) максимум трижды; определённые 4xx кроме 429 не повторяет. Старый клиент без event ID продолжает работать. Обновлены app, worker и RU offer worker; хэши source/runtime совпали. Alex `scrape` после выпуска: RU task completed `ok=true`, 3593 лида сохранены в PostgreSQL и Sheets, затем Redis task компактна (3150 байт), parent `idle` без отправки. Это проверка восстановления пути в одном прогоне, не доказательство отсутствия будущих сетевых отказов. Доказательства `C:/Users/admin/Desktop/Project/outputs/ru-control-retry-20261018/EVIDENCE.md`; runtime source `/root/TrafficHub/traffic_hub/{remote_worker.py,services/remote_autolead.py,api/routers/remote_autolead.py}` и `/root/TrafficHub/services/source_control.py`.

## Реальная параллельность трёх owner — проверено 2026-10-18, 21:47 МСК

Job `32934eee1ead4d70ad264a97e85a43d8` (admin), `c5a2468b16904f38bad09cbb0e31ad08` (Дмитрий), `a709de32d350471c95fc14b2e2158fbd` (Alex) одновременно были `running`, Redis `active=3`, queue=0. Admin и Дмитрий завершились `idle`; у Alex удалённый `rabota_collect` был claimed, но вернул `ru_unavailable/control_channel_unavailable`, а HH credentials отсутствуют и SuperJob не реализован в full cycle. Это доказывает независимый старт owner jobs, но не гарантирует доступность каждого удалённого источника при такой нагрузке. У Дмитрия шесть `offer_autofill` task завершились `ok=true`, job sent=26/uncertain=0. После terminal active/processing/queue 0, Redis 335.11/512 MiB; пиковый наблюдавшийся срез 355.28 MiB. Код: `/root/TrafficHub/traffic_hub/services/{job_queue,job_runner,remote_autolead}.py`; доказательства `C:/Users/admin/Desktop/Project/outputs/traffic-cycle-20261018/PARALLEL.md`.

## Большие результаты сбора Работа.ru — проверено 2026-10-18

После Redis `OutOfMemoryError` при лимите 512 MiB (worker log 10:35:50 МСК) read-only разбор показал 202 remote task keys общим размером 322 322 524 байта. Семь завершённых `rabota_collect` по 5,2–5,5 тыс. анкет занимали по 25–27 МБ каждая; прежний TTL для них 7 суток. Причина точного пика в момент OOM не измерена. Job admin `26bc09e9158b4afb8ab868153829aa49` позже стал stale-lock error.

Server commits `ec14d9654`, `dbbe91a11`, `23c5e3cf8`: `traffic_hub/services/remote_autolead.py` через CAS убирает список `result.leads` у завершённой задачи только для совпадающих owner и parent job; `traffic_hub/services/job_runner.py` вызывает это после сохранения в PostgreSQL и `HhDelivery.stage()` с долговечным checkpoint. Строгий режим БД оставляет большой исходный результат, если хотя бы одна строка не сохранилась. Сводка и `persisted_lead_count` остаются. Worker image `traffichub-worker-collect-compaction:23c5e3cf8` опубликован, app не менялся. Admin job до последнего safety commit подтвердил 411 обработанных анкет и 4103 байта в Redis task после compaction, завершился `idle`; после последнего выпуска Redis 337.29 MiB/512 MiB, active/processing 0. Старые результаты оставлены до TTL. Доказательства: `C:/Users/admin/Desktop/Project/outputs/traffic-cycle-20261018/EVIDENCE.md`; текущий план: [[04_План/Сейчас/Что происходит сейчас]].

## Текущее состояние, проверено 2026-10-16

Проверка 2026-10-16 20:00 МСК: origin source HEAD 215a85aca; origin app/worker images traffichub-resilient-cycle-{app,worker}:215a85aca; RU image traffichub-ru-resilient-cycle:8868288a4, REMOTE_WORKER_MODE=per-task. Отдельная задача получает собственный процесс, RemoteClient и контекст credentials; общего фиксированного owner-пула нет. Физические лимиты RU (4 GiB, 2.5 CPU, 1024 PID) сохраняются.

Причина жалобы «2 лида 17 минут»: задача оффера была создана 15 октября в 23:27:13, до отмены 23:43:05 не получила claim. Это ожидание старого RU исполнителя, а не доказанные 17 минут обработки двух лидов. Источник: `C:/Users/admin/Desktop/Project/outputs/admin-slow-stop-20261016/EVIDENCE.md`.

Проверки релиза: 53 целевых теста в предыдущем release и безопасный барьер шести синтетических owners; реальные параллельные production-кампании не запускались. Доказательства: `C:/Users/admin/Desktop/Project/outputs/elastic-users-20261016/EVIDENCE.md`; текущие контейнеры и код: `C:/Users/admin/Desktop/Project/outputs/baza-reconcile-20261016/origin.txt`, `C:/Users/admin/Desktop/Project/outputs/baza-reconcile-20261016/ru.txt`. Отдельная видимость стадии ожидания в UI остаётся задачей, не подтверждённым исправлением.

## Полный цикл, Sheets и reconciliation — 2026-10-16

Проверка 2026-10-16 20:00 МСК: origin source HEAD 215a85aca; origin app/worker images traffichub-resilient-cycle-{app,worker}:215a85aca; RU image traffichub-ru-resilient-cycle:8868288a4, REMOTE_WORKER_MODE=per-task. Task follow-ups c0341c000/215a85aca preserved aggregate delivery reasons; intermediate commits 403e1cc64/80788e8fd touched another feature. Origin public health и подписанный RU control health успешны; app/worker/RU healthy; source/runtime SHA совпали.

Admin job 9df78968d6df4036bd64b30fe54e8b6b: Rabota 632 collected/2 saved; HH 5 saved по одному рабочему подключению, второе revoked; Sheets подтвердил 7 строк, owner outbox пуст; PostgreSQL aggregate за интервал подтвердил 2 response и 5 hh_ru. Все 12 admin offer mappings были отключены, отправлено 0 форм. Исправленный summary: 7 no_offer, uncertain 0. После выпуска job 239e7de073a1492597af183295c1d42b вернулся idle: Rabota 632 проверены без новых, HH без новых по рабочим подключениям; revoked connection показан partial; legacy backlog не выбран.

Пустой набор lead_results при успешном RU ответе теперь fail-closed: parent не считает неизвестные строки обработанными; task сохраняется как uncertain и изолируется owner-scoped quarantine до сверки. Отказ одного HH подключения не запрещает выполнение остальных.

Изменения, валидация, rollback и остаточные ограничения: C:/Users/admin/Desktop/Project/outputs/resilient-cycle-20261016/EVIDENCE.md.
Разбор результата и причины «processed без категории»: [[03_Ошибки/Расследования/2026-10-16 Полный цикл, Sheets и классификация пустого ответа RU]].

## Назначение

Redis хранит краткоживущий runtime state очереди Autolead jobs:

- `traffic_hub:jobs:progress:<owner>` — progress counters из `utils/state.py`;
- `traffic_hub:jobs:state:<owner>` — статус job из `traffic_hub/services/job_queue.py`;
- `traffic_hub:jobs:stop:<owner>` — stop flag;
- `traffic_hub:jobs:queue` — очередь задач;
- `traffic_hub:jobs:active` — active owners.

## Подтверждённое поведение

После fix `e4818e56a` progress/state/stop keys не должны жить бесконечно:

- progress TTL: 7 дней;
- job state TTL: 7 дней;
- stop flag TTL: 6 часов.

## Почему так

Redis в этом контуре — runtime cache. Источник истины по пользователям, лидам, логам и настройкам находится в PostgreSQL/control store. Вечные Redis keys создают риск stale UI/status после рестартов, тестовых запусков и debug-сессий.

## Проверка

На сервере:

```bash
docker exec traffichub_redis redis-cli ttl traffic_hub:jobs:progress:artem
docker exec traffichub_redis redis-cli ttl traffic_hub:jobs:state:artem
```

Ожидаемо: положительное число секунд, не `-1`.

## Связанные заметки

- [[2026-06-23 TrafficHub full senior audit]]
- [[2026-06-24 Redis job state TTL hygiene]]
- [[Autolead runtime]]


## Ожидание RU очереди admin и ложная ошибка остановки — 2026-10-16

Пользователь остановил admin job0e7a70d751764ca39fac592b9e2b078d после долгой обработки2лидов. Runtime доказал: job23:18:56; rabota_collect created23:18:59/claimed23:25:22, очередь6м23с; HH2лида получены23:27:06 и Sheets сохранены23:27:13. offer_autofill task e1fb3a31dfb445ca9abed869728ec296 создан23:27:13, claimed_at=null, lead_count2, canceled23:43:05 после user stop23:43:04. Поэтому15м51с после выгрузки — ожидание очереди, отправки этой задачей не начинались. Другой owner task4ec51fff963c44f09e1f3d1e6f09200a,25leads, claimed23:33:36/completed23:47:40, подтверждает конкурирующую занятость в части интервала (не единственная доказанная задача на всём интервале).

Причина неверного ERROR: remote_autolead.wait_result после !_parent_active вызывает _cancel_inactive и raises RemoteAutoleadError('parent job stopped or replaced'); job_runner.run except BaseException без проверки user stop записывает job_error. job_runner имеет несвязанный dirty diff, не трогался. Недостаток наблюдаемости: отправка в очереди выглядит обработкой, нет явного ожидания RU capacity. Не делать вывод о медленной отправке2лидов или о повторной отправке: claimed отсутствует. Код/очередь/данные не менялись, повторный запуск не выполнялся.
Evidence C:/Users/admin/Desktop/Project/outputs/admin-slow-stop-20261016/tasks.txt, queue-overlap.txt. Следующее исправление: явный queued статус и elapsed, user stop -> job_stop, затем проверить ограниченную справедливость общей RU очереди без изменения idempotency/quarantine и без умножения send workers вслепую.

## Исправление RU параллельности и ручной остановки — 2026-10-16

Порученные ошибки исправлены commit `baae3e4dc`: RU offer worker теперь supervisor4 независимых polling processes (spawn; каждый сохраняет отдельное isolated execution), default1/max8. Разные users выполняются параллельно до4 задач; сверх лимита очередь сохраняется. Lease/CAS/idempotency/quarantine/daily-limit не менялись; одна parent job наowner и последовательные batches остались. Origin execute_job при stop flag своего job_id завершает job_stop/idle без ERROR; replaced/foreign job и реальные сбои не скрываются.

51 targeted checks PASS, включая реальное пересечение2 процессов, stop/replaced и lease/owner guards. Выпуск при activejobs/remote=[]; origin worker-only, app unchanged. RU existing image сохранён, новый runtime4pollersready/healthy/freshheartbeat, public health200; ограничения4GiB/2.5CPU/1024pids. Старый RU контейнер остановлен и сохранён для rollback. Исходный dirty job_runner diff уже был live; в commit включён только свой stop-hunk, чужие изменения сохранены. Доказательства `C:/Users/admin/Desktop/Project/outputs/parallel-stop-20261016/EVIDENCE.md`, `tests-final.txt`, `deploy-origin.txt`, `deploy-ru.txt`, `runtime-pollers.txt`. Реальные повторные отправки не запускались.

## Уточнение: без общего фиксированного лимита пользователей — 2026-10-16

Прямое уточнение пользователя отменяет fixed4 как целевой режим. Commit `88b977d54`: RU offer worker включён в `REMOTE_WORKER_MODE=per-task`, отдельный процесс на каждую принятую задачу; controller не ждёт свободного shared slot и не имеет фиксированного ограничения числа owners. Старый fixed mode сохранён для совместимости, но на RU offer runtime не используется. Owner parent/batch sequencing, stop fix baae3e4dc, CAS/lease/idempotency/quarantine сохранены. Физические RAM/CPU/PID server limits остаются; бесконечная вычислительная ёмкость и автоматическое добавление серверов не заявляются.

53 targeted testsPASS. В installedRUконтейнере6 synthetic owners реально пересеклись до завершения любого, без реальных запросов/форм; liveper-task/healthy/freshheartbeat/publichealthok. Originapp/worker не пересоздавались. Rollback — stoppedcontainer traffichub_offer_worker_before_elastic_20261016 после idle. Evidence `C:/Users/admin/Desktop/Project/outputs/elastic-users-20261016/EVIDENCE.md`, `tests.txt`, `live-safe-smoke.txt`, `health.txt`, `deploy.txt`.

## Восстановление Redis и RU workers — 2026-10-26

Origin Redis не запускался из-за malformed multipart AOF; main worker перезапускался, а RU consumers получали 401 от подписанного control API: проверка nonce зависит от Redis. Fingerprints shared key совпали. `redis-check-aof` на копии нашёл полный префикс 41 369 477 байт и незавершённый хвост 123 байта. После проверенной локальной копии всего Redis-тома удалён только этот хвост; завершённые команды и base RDB побайтно сохранены. Очереди и active owners были пусты до запуска main worker; сохранённые 85 remote tasks имели terminal state. RU процессы не перезапускались.

Проверено: app/worker/Redis/PostgreSQL и оба RU workers healthy, Redis PONG/AOF write ok, signed control health PASS. Проверка origin enqueue → RU HH consumer → encrypted completion вернула HTTP 403 forbidden от HH `/me` без OAuth; это проверка транспорта, не авторизации работодателя. Сбор лидов и отправка форм не запускались. Код приложения не менялся. Доказательства: `C:/Users/admin/Desktop/Project/outputs/ru-worker-recovery-20261026/EVIDENCE.md`, `smoke.json`, `ru-health.json`, `dry-run.json`. Проверенный полный архив хранится только локально: `C:/Users/admin/Desktop/Project/backups/2026-10-26/redis-ru-recovery/`.

Операционный отчёт зафиксирован в серверном commit 4e16bfc6f; Harness workstream ru-worker-recovery-20261026 CLOSED. Временные серверные backup/test-copy удалены после проверки; локальный архив сохранён. Public health с RU HTTP 200. Итог: outputs/ru-worker-recovery-20261026/final.json.
