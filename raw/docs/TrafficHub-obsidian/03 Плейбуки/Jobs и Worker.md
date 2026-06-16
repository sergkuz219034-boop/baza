# Jobs и Worker

## Когда использовать

- кнопка `Выгрузка`, `Полный цикл`, `Рассылка`, `SuperJob` не стартует;
- UI зависает в `В РАБОТЕ` или `В ОЧЕРЕДИ`;
- повторный запуск даёт конфликт;
- пользователь говорит `ничего не работает`.

## Быстрая проверка

1. Health:
   - `GET https://traffic-hubcrm.ru/api/health`
2. Контейнеры:
   - `autolead_server_bot`
   - `traffichub_worker`
   - `traffichub_redis`
   - `traffichub_postgres`
3. Redis queue:
   - `traffic_hub:jobs:queue`
   - `traffic_hub:jobs:state:<owner>`
   - `traffic_hub:jobs:active`
   - `traffic_hub:jobs:events`
4. Логи:
   - `docker logs autolead_server_bot`
   - `docker logs traffichub_worker`
5. Heartbeat worker:
   - `/app/data/runtime/worker.heartbeat`
   - live healthcheck считает worker живым, если heartbeat моложе `180` секунд

## Что считать нормой

- первый `POST /api/jobs/run`:
  - `200`
  - `status=queued`
- в live-логе сразу появляются owner-scoped строки:
  - `Полный цикл: в очереди` / `Рассылка: в очереди`
  - `Полный цикл: запущен` / `Рассылка: запущен`
- при долгом выполнении:
  - heartbeat примерно раз в `15` секунд
  - в текущем UI это обычная timestamp-строка вида `Полный цикл выполняется` / `Рассылка выполняется`
  - heartbeat не должен жить как transient spinner и не должен мгновенно исчезать
  - детальные counters не должны засорять пользовательскую ленту
- structured log payload не должен терять `ts` в `dashboard/app.js`; historical parser допустим только для старых plain-text строк
- stop request должен сразу переводить state в `stopping` и писать красную строку `⛔ <команда> остановка`
- если owner subprocess завис в Playwright/network wait:
  - worker сначала отправляет мягкий stop (`SIGTERM`);
  - затем после короткого grace period принудительно завершает owner subprocess;
  - канонический ориентир по live runtime: stop не должен ждать полный browser timeout.
- повторный запуск того же owner, пока job жива:
  - `202`
  - `already_running=true`
- завершённая задача:
  - Redis state `status=idle`
  - `command=null`
  - `last_command` хранит последнюю выполненную команду для финального статуса/UI
  - `started_at` не должен исчезать после завершения
  - `finished_at` установлен
  - в live-логе есть строка `Полный цикл: завершён` или `Полный цикл: остановлен`
  - подтверждённый owner-scoped `app_log` snapshot для `admin` на `2026-06-16`:
    - `2026-06-16 00:02:51 [i] Рассылка: запущен`
    - `2026-06-16 00:04:58 [OK] Рассылка: завершён`
- устаревшая busy-блокировка:
  - после ~`6` часов должна быть автоматически переведена в `error`

## Подтверждённый runtime на 2026-06-14

- Историческая single-flight модель больше не канон.
- Причина старого ограничения была подтверждена:
  - `traffic_hub/services/job_runner.py` использовал `redirect_stdout()`;
  - `modules/vbiv_bot.py` держал global `_active_ctx`;
  - thread-параллельность в одном worker process была unsafe.
- Актуальная безопасная модель:
  - queue/state остаются per-owner;
  - исполнение идёт через subprocess-per-owner;
  - `traffichub_worker` может держать несколько owner jobs одновременно;
  - stop/progress/app-log остаются owner-scoped через Redis и process-local logging setup.
- От `2026-06-16` добавлен ещё один live-invariant:
  - после любых server-side правок sender/runtime нельзя считать задачу исправленной только по `autolead_server_bot`;
  - нужно сверять live-код и image обеих сторон:
    - `autolead_server_bot`
    - `traffichub_worker`
  - иначе можно получить ложный smoke-pass в web container и старый код в реальном queue worker.
- На текущем live server safe default:
  - `WORKER_MAX_PARALLEL_OWNERS=2`
  - причина — машина `2 vCPU / ~4 GB RAM` с заполненным swap и высоким load average.
- Runtime proof:
  - `debug-worker-a` и `debug-worker-b` одновременно были `running` с одинаковым `started_at=2026-06-14 16:32:56`.
  - `debug-worker-a..d` подтвердили batched execution `2 + 2`.

## Подтверждённые файлы

- `api/routers/jobs.py`
- `traffic_hub/services/job_queue.py`
- `traffic_hub/services/job_runner.py`
- `traffic_hub/worker.py`
- `api/ws_manager.py`
- `dashboard/app.js`

## Что реально делает каждая кнопка

- `POST /api/jobs/run {command:"send"}`:
  - читает `utils.database.load_leads_for_send(days=3650)`
  - не обрабатывает `retry_queue`
  - значит проверка конкретного оффера через кнопку `Рассылка` должна смотреть на `leads` + `offer_mapping`, а не на `retry_queue`
- `POST /api/jobs/run {command:"run"}`:
  - запускает `services.leads_service.run_full_cycle()`
  - именно здесь есть фаза `process_retry_queue()`
  - если нужно проверить retry/offline errors, это делается через `Полный цикл`, а не через `Рассылка`

## Типовые причины

### 1. Задача реально занята

- Симптом:
  - второй запуск даёт `already_running`
- Проверка:
  - Redis state owner в `queued/running/stopping`
- Вывод:
  - не баг, если первый run действительно ещё жив

### 2. UI показывает старый статус

- Симптом:
  - в Redis уже `idle`, а пользователь видит подвисший pill
- Проверка:
  - сравнить `/api/jobs/status` и визуальный pill
- Замечание:
  - это фронтовая или websocket/poll проблема, не обязательно worker bug

### 2a. Пользователь думает, что задача зависла

- Симптом:
  - pill показывает `В РАБОТЕ`, но в live-логе тишина
- Проверка:
  - должны быть строки `в очереди` и `запущен`
  - если run длинный, каждые ~`15` секунд должен приходить heartbeat `Полный цикл: выполняется` / `Рассылка: выполняется`
- Вывод:
  - отсутствие heartbeat при живом `running` состоянии уже считать диагностическим сигналом, а не нормой

## Подтверждённый live UX логов

- backend режет шум в:
  - `api/server.py`
  - `utils/runtime_logging.py`
- sender-runtime дополнительно обязан отдавать короткие ошибки:
  - `modules/vbiv_bot.py` должен логировать сжатый текст ошибки без Playwright `Call log`
  - если в UI снова видны многострочные `Page.goto ... Call log ...`, значит regression именно в sender/runtime, а не только во frontend-фильтре
- history/snapshot путь тоже должен быть чистым:
  - `api/server.py::_normalize_dashboard_message()` обязан обрезать `Call log` и схлопывать multiline в одну строку
  - это защищает не только websocket-live, но и `GET /api/logs`
- frontend не должен плодить heartbeat-дубли:
  - `dashboard/app.js`
  - heartbeat статуса задачи не должен рендериться как `.log-spinner`
  - `.log-spinner` допустим только для реально временных сообщений, а не для owner job heartbeat
- в нормальном сценарии пользователь должен видеть:
  - статусные строки задачи;
  - прикладные строки результата оффера:
    - `[OK] Оффер ...`
    - `[~] Оффер ...`
    - `Ошибка ...`
- пользователь не должен видеть как business log:
  - `Retry queue: ...`
  - `Sheets upload: ...`
  - `-> Заполняем: ...`
  - `Скриншот ошибки: ...`

## Отдельно про flaky offer landing

- Для `lovko`-офферов подтверждён нестабильный upstream `goto`:
  - страница может остаться на `about:blank`
  - title может остаться `Loading ...`
- Каноническая проверка после 2026-06-13:
  - sender должен делать ограниченный retry открытия оффера;
  - `lovko` — до `3` попыток;
  - остальные платформы — до `2` попыток.
- Если `alex/Ozon` снова массово падает:
  1. проверить, что в live `modules/vbiv_bot.py` остался retry-block;
  2. повторить 5-кратный smoke для `https://tracking.lovko.pro/click?pid=4126&offer_id=22`;
  3. только после этого считать проблему снова runtime-багом, а не временным upstream timeout.
- От `2026-06-15` есть ещё один подтверждённый runtime-contract:
  - каждая анкета должна открываться в отдельном browser instance;
  - reuse одного browser между офферами больше не канон, потому что загрязняет partner-click session и даёт cross-offer regressions.
  - практический смысл: каждый partner click должен идти из нового браузера, иначе часть партнёрок считает переход неуникальным или наследует предыдущую сессию.

## Отдельно про `Воксис` / `leadsu`

- На `2026-06-14` подтверждены два разных класса дефектов:
  - blank DOM перед submit: [[01 Расследования/2026-06-14 Leadsu blank DOM before submit on Voxys]]
  - ложный `submit not found` на непустом DOM: [[01 Расследования/2026-06-14 Leadsu false submit not found on non-blank Voxys DOM]]
- На `2026-06-15` подтвержден ещё один runtime path:
  - success popup реально появлялся, но общий `success_selector` мог не сработать, если видимым был не `first` match комбинированного селектора;
  - landing `pxl.leads.su` через proxy оставался intermittent и требовал отдельного retry budget для `leadsu`.
- На том же live debug позже подтверждено уточнение:
  - проблема не в том, что proxy нужен всем формам;
  - `Playwright + proxy` для `pxl.leads.su` может стабильно давать `ERR_TIMED_OUT`, хотя тот же URL без proxy открывается;
  - `lovko/Ozon` при этом остаётся proxy-dependent path.
- Если в live логах снова есть:
  - `leadsu: кнопка submit не найдена`
  - `leadsu: форма не подтверждена после отправки`
- Проверять по шагам:
  1. существует ли debug HTML и пустой ли он;
  2. есть ли в debug HTML `#send_form`;
  3. применён ли hotfix `modules/platforms/leadsu.py` в source tree и контейнере;
  4. применён ли runtime fix `modules/platforms/base.py` для any-visible success selector;
  5. не идёт ли `pxl.leads.su -> voxys-rabota.ru` через proxy, хотя должен идти direct;
  6. сверить с [[01 Расследования/2026-06-15 Voxys leadsu success selector и intermittent goto timeout]].

### 3. Worker упал или не забрал задачу

- Симптом:
  - queue length > 0
  - state остаётся `queued`
- Проверка:
  - `docker logs traffichub_worker`
  - container status
  - возраст `/app/data/runtime/worker.heartbeat`
- Дополнительная развилка:
  - если после worker restart queued/running owner внезапно стал `idle` или `error` без длинной истории логов:
    - проверить startup reconciliation в `traffic_hub/worker.py`
    - queued/running job может быть сброшен как maintenance side-effect, а не как бизнес-ошибка

### 4. Playwright упал внутри run

- Симптом:
  - логи worker/bot содержат browser/form/runtime ошибки
- Исторически подтверждённый баг:
  - cross-thread `context.close()` ломал greenlet и давал `Cannot switch to a different thread`
- Текущий статус:
  - исправлено в `modules/vbiv_bot.py`

### 5. Логи одного owner попали другому owner

- Симптом:
  - в `app_log` или UI у пользователя появляются чужие `Сбор лидов`, `-> Заполняем`, `[OK] Оффер`
- Проверка:
  - поднять одновременно jobs для двух owner и сверить owner-specific `app_log`
- Подтверждённая историческая причина:
  - небезопасная комбинация `redirect_stdout()` + параллельные worker-thread
- Текущий статус:
  - thread-параллельность больше не используется;
  - owner jobs разведены по subprocess;
  - проверка на `debug-worker-a` и `debug-worker-b` подтвердила owner-scoped app logs без пересечения.

### 6. `/stop` не ощущается мгновенным

- Симптом:
  - пользователь нажимает `Остановить`, но stop визуально приходит поздно;
  - или в логе нет явного `⛔` на stop-request.
- Проверка:
  - owner state должен почти сразу стать `stopping`;
  - в `app_log` должны появиться:
    - `⛔ <команда> остановка`
    - затем `⛔ <команда> остановлен`
- Подтверждённый historical root cause:
  - `modules/vbiv_bot.py` использовал `stop_event.wait(timeout=delay)` и не будился owner-specific stop-флагом;
  - `dashboard/app.js` удалял `⛔`, а старый `api/server.py` мог логировать stop-request как `[i]`.
- Подтверждённый live root cause второго уровня:
  - `interrupt_current_context()` из API не может остановить Playwright другого subprocess;
  - `traffic_hub/worker.py` раньше ограничивался `process.terminate()` и не эскалировал зависший owner subprocess.
- Актуальный live fix:
  - `traffic_hub/worker.py` держит owner-scoped stop grace timer;
  - при `stopping` worker повторно проверяет живой subprocess и после grace period делает `process.kill()`.

## Что документировать после каждого инцидента

- owner username
- команда (`upload`, `run`, `send`, `superjob`)
- состояние Redis до/после
- строки `autolead.log`
- HTTP-ответ `/api/jobs/run`
- был ли баг только в UI или реально в worker/runtime

## См. также

- [[01 Расследования/2026-06-07 Ничего не работает]]
- [[01 Расследования/2026-06-11 Autolead owner-scoped jobs и UI-логи]]
- [[01 Расследования/2026-06-12 Realtime статус задачи в live-логе]]
- [[01 Расследования/2026-06-14 Heartbeat статус задачи мигал как transient spinner]]
- [[01 Расследования/2026-06-14 Frontend затирал ts у структурированных log messages]]
- [[01 Расследования/2026-06-14 Stop request lag и stop-сигнал без ⛔]]
- [[04 Сущности/Job Queue]]
- [[05 Решения/Очередь задач через Redis и worker]]
