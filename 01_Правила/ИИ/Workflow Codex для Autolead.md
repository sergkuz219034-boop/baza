# Workflow Codex для Autolead

## Проверка полного пути исполнения — уточнение 2026-10-16

Проверять origin enqueue → RU claim → фактическое выполнение → terminal state. Измерять ожидание отдельно от обработки: время между созданием и claim нельзя называть временем выгрузки лидов. Проверка параллельности должна доходить до RU; текущий режим `per-task` проверен безопасным барьером на шести синтетических owners без отправок. Четыре общих слота — исторический промежуточный вариант, не требуемое поведение.

При остановке проверять stop flag вместе с идентичностью job_id; отдельно проверять replaced/foreign job и реальные исключения. После сборки из overlay сверять содержимое затронутых файлов с каноническим репозиторием, а также сохранность недавних релизов: healthy не доказывает наличие нужной версии отчёта.

Доказательства: `C:/Users/admin/Desktop/Project/outputs/elastic-users-20261016/EVIDENCE.md`, `C:/Users/admin/Desktop/Project/outputs/parallel-stop-20261016/EVIDENCE.md`, `C:/Users/admin/Desktop/Project/outputs/baza-reconcile-20261016/runtime-files.txt`.

Короткий канонический маршрут для задач, где основной объект работы: `Autolead`.

Используется вместе с `[[01_Правила/ИИ/Workflow Codex для дебага и разработки]]`, а не вместо него.

## Когда открывать сразу

- баг в `Autolead` dashboard;
- проблема owner-scope у settings, offers, leads, stats;
- scheduler / full-cycle / retry / queue проблема;
- bug в Google Sheets, Rabota.ru, offers automation;
- вопрос по operational runtime `Autolead`, а не по embedded `TrafficHub CRM`.

## Главный контур

1. Сначала прочитать `[[02_Код/Эксплуатация/Доступ и подключения]]`, если задача затрагивает live.
2. Держать в голове канон repo: product-код живёт только в `/root/TrafficHub`.
3. Для кода начинать с одной из root-entrypoint зон:
   - web/auth/dashboard/ws: `api/server.py`
   - runtime/business flow: `services/leads_service.py`
   - jobs и статусный fan-out: `api/routers/jobs.py`, `traffic_hub/worker.py`
   - settings/import/export: `api/routers/settings.py`
   - owner/runtime gate: `api/autolead_access.py`
4. Для каждой гипотезы подтверждать один runtime-факт:
   - `/api/health`
   - конкретный endpoint
   - конкретный лог
   - конкретный контейнер
   - один targeted test
5. После фикса проверять не только `admin`, но и обычный user-контур.
6. После нового знания обновлять каноническую `baza`; GitHub-синхронизация — по отдельному запросу.

## Инварианты Autolead

- `Autolead` нельзя проверять только на `admin`.
- Любой settings/runtime/profile/auth path должен быть owner-scoped.
- Новые пользователи не должны получать мусорные defaults от `admin`.
- Scheduler, queue и full-cycle должны работать по всем релевантным owners, а не по одному user.
- Ошибка формы, оффера или интеграции не должна тихо ломать весь operational цикл.
- Если bug виден у одного пользователя, считать его общим, пока код или runtime явно не доказали owner-specific природу.

## Быстрый маршрут по типу симптома

### UI / dashboard

- смотреть `api/server.py`, `dashboard/index.html`, `dashboard/app.js`, `dashboard/style.css`;
- проверять hash-route, tab context, auth/session и owner-gated sections;
- если меняется UI-навигация, проверять связанные тесты маршрутов.

### Settings / auth / import-export

- смотреть `api/routers/settings.py` и `api/autolead_access.py`;
- проверять owner привязку secrets, service account, Rabota.ru token и runtime profile;
- при import/export отдельно проверять, не утекает ли общий `secrets` контур.

### Leads / offers / full cycle

- смотреть `services/leads_service.py`, `modules/*`, `api/routers/jobs.py`;
- проверять статусные события, retry queue, repeat protection и деградацию при частичных ошибках;
- если симптом связан с live-циклом, различать web-loop и worker-loop.

### Scheduler / worker / deploy

- смотреть `traffic_hub/worker.py`, scheduler path, container logs и live compose-контур;
- подтверждать, что новый код попал в `/app`, а не остался только в host repo;
- после deploy проверять `/api/health`, `docker compose ps` и нужный smoke.

## Стандарт завершения

Задача по `Autolead` закрыта только если применимые шаги подтверждены:

- первопричина локализована;
- исправление проверено на общем owner-контуре;
- локальный server repo commit выполнен при изменении кода;
- push и GitHub checks подтверждены только при отдельно выбранном GitHub-контуре;
- live runtime healthy;
- wiki обновлена;
- GitHub-синхронизация `baza` выполнена только при отдельном запросе.

## Связанные заметки

- [[01_Правила/ИИ/Workflow Codex для дебага и разработки]]
- [[01_Правила/ИИ/Правила для ИИ]]
- [[03_Ошибки/Отладка/Рецепт отладки]]
- [[01_Правила/Плейбуки/Fast debug loop]]
- [[02_Код/Эксплуатация/Воркеры и расписание]]
- [[02_Код/Эксплуатация/Конфигурация]]

## Каноническое правило: три сбоя API отключают источник

Статус: обязательное требование пользователя от 2026-10-04.

- Если API источника не отвечает три последовательные попытки, источник автоматически отключается у затронутого owner. Правило распространяется на все API-источники, а не только Работа.ru.
- Счётчик ведётся отдельно для пары owner + источник. Успешный ответ сбрасывает его. Внутренние повторы и перебор proxy/direct одного обращения считаются одной попыткой после исчерпания маршрутов.
- Неответ — timeout, отказ соединения либо отсутствие пригодного ответа API. Корректный ответ с бизнес-отказом кандидату не является неответом.
- После третьего сбоя сохраняется enabled=false с причиной отключения. Четвёртое обращение блокируется, включая обращения из уже запущенных циклов; старый snapshot настроек не должен обходить блокировку.
- Токены, настройки, история и необработанные кандидаты сохраняются. Другие источники и пользователи не отключаются.
- Автоматическое повторное включение и бесконечные retries запрещены. Включение выполняется вручную через «Источники» и сбрасывает счётчик.
- Пользователь получает одно уведомление об автоматическом отключении с названием источника и причиной, без токенов и адресов прокси.

Проверка реализации должна доказать: два сбоя оставляют источник включённым; третий отключает; четвёртый не выходит в сеть; успех сбрасывает счётчик; состояние сохраняется между задачами/restart и изолировано по owner/источнику.

Состояние реализации проверено 2026-10-04: в live `services/source_control.py` есть сохраняемые ручные переключатели, но счётчика/автоотключения по этому порогу нет. Требование не выдавать за внедрённую функцию до реализации и targeted runtime smoke. Доказательства: `C:/Users/admin/Desktop/Project/output/source-api-policy-20261004/source_control.py` и `evidence.json`. См. [[04_План/Разработка/Технический долг]].


## Проверенные send-safety ограничения — 2026-10-07, patch до релиза

При исправлении удалённой отправки проверять четыре инварианта: действующий parent
и stop flag; конечную lease даже при сетевом сбое; реальные owner daily counters;
обязательную читаемую историю перед отправкой. Сбой чтения не означает пустую историю.
Для Android mailing idempotency должна быть общей между устройствами кампании,
а повторная привязка телефона не должна сбрасывать дневной лимит. Неопределённый
результат после authorize требует проверки; автоматический replay запрещён.
Инварианты подтверждены целевыми тестами patch b4d6ea169; live deploy ещё pending.

Доказательства: `C:/Users/admin/Desktop/Project/outputs/high-fixes-telegram-20261007/EVIDENCE.md`. PR: https://github.com/sergkuz219034-boop/TrafficHub/pull/257.

## Согласование production-контура — 2026-10-08

Обычная порученная правка следует прямому production-контуру общего workflow.
Полный suite — только по явному запросу; проверки выбираются по изменённому
поведению и зависимостям. Доказательства: C:/Users/admin/Desktop/Project/outputs/harness-fix-20261008/completion-check.md.


## Проверка нового аккаунта и границ владельца — 2026-10-13

- Для личных данных проверять owner и tenant также у роли Admin; роль сама по себе не разрешает чтение чужого кабинета.
- При совпадении логина со старыми runtime-записями проверять дату регистрации текущего `users` identity. Записи до неё не должны автоматически переходить новому аккаунту. Для legacy Autolead действует `utils/owner_epoch.py`; для Telegram — `utils/telegram_ownership.py`.
- Новый профиль явно начинает с `enabled=false` для Работа.ру, HH.ru, SuperJob и Avito; расписание и Google Sheets выключены. Существующие явные настройки сохранять.
- Проверять списки, прямые ID, экспорт, агрегаты и запоздавшие ответы UI. Персональные API-ответы имеют `Cache-Control: private, no-store`.

Проверено 2026-10-13, app `be8bacc15f75b677480b6ecc95b9c93ff73caa36`. Источники: `/root/TrafficHub/{services/leads_service.py,traffic_hub/api/ownership.py,utils/owner_epoch.py,utils/telegram_ownership.py,api/server.py}`; доказательства `C:/Users/admin/Desktop/Project/outputs/messenger-isolation-20261013/` (`tests.log`, `epoch-pg.log`, `live-smoke.json`, `export-safety.json`). Worker обновлён 2026-10-13 после явно разрешённой штатной остановки alex и admin; healthy, worker-isolation-smoke.json PASS. Связано: [[02_Код/Код/Бэкенд]], [[03_Ошибки/Отладка/Каталог ошибок]].

## RU — канонический исполнитель анкет для всех пользователей — 2026-10-13

Прямое требование пользователя: исполнение анкет должно идти через RU у всех текущих и будущих пользователей. Production использует `REMOTE_AUTOLEAD_ENABLED=true`, `REMOTE_AUTOLEAD_OWNERS=*`; ограничения двумя логинами отменены. При восстановлении конфигурации и выпуске новых образов сохранять wildcard и проверять общий owner-контур. Owner/tenant, подпись, lease, остановка и защита повторной отправки обязательны.

Проверено в app и worker: admin, обычный и будущий owner разрешены; пустой owner запрещён. RU offer worker running, публичный health ok, app/worker healthy. Обнаружено и исправлено расхождение: прежний worker не поддерживал wildcard. Узкий производный образ сохраняет его baseline и меняет только `enabled_for`. Коммиты `2df5c0c95`, `13bda344f38192b30f61a963e998a8527758e03f`. При проверке анкеты не отправлялись.

Доказательства: `C:/Users/admin/Desktop/Project/outputs/ru-forms-all-users-20261013/live-smoke.txt`; сервер `/root/TrafficHub/deploy/ru-all-users-20261013/`. Связано: [[02_Код/Эксплуатация/Конфигурация]].

## Удаление отдельной ежедневной проверки HH — 2026-10-13

Пользователь уточнил: «HH.ru · ежедневная проверку мы убирали». Этот отдельный daily/resume механизм не возвращать под новым названием. Сохранять обычный owner-scoped импорт HH и полный цикл. Проверка2026-10-13 выявила расхождение требования и runtime: admin flag всё ещё true, callbacks daily/resume остаются. Удаление не считать завершённым; H-01 в [[03_Ошибки/Расследования/2026-10-13 Аудит TrafficHub и прогрев на эмуляторе]]. Доказательство: C:/Users/admin/Desktop/Project/outputs/project-audit-emulator-20261013/hh-retired-check.txt.

## Параллельная работа пользователей — 2026-10-14
Прямое требование пользователя в текущем чате: все существующие и новые пользователи должны работать одновременно с другими. Общий worker запускает независимые owner subprocesses (`WORKER_MAX_PARALLEL_OWNERS=0`), RU routing использует `REMOTE_AUTOLEAD_OWNERS=*`, без ручного добавления логинов. Это не отменяет owner isolation, один job на owner, quota/rate limits, bounded внешние consumer ресурсы и защиту одинакового HH менеджера. Restart recovery не должен возвращать в очередь/сбрасывать задачу со свежим heartbeat другого worker. Подтверждение runtime и 13 целевых tests: `C:/Users/admin/Desktop/Project/outputs/hh-one-second-20261014/EVIDENCE.md`; commit187a79324. Legacydispatcher с текущимAlex пока сохранён; единый физический контейнер не является требованием пользователя.

## Каноническая дата собранных лидов — 2026-10-14
По прямому указанию пользователя «должна быть везде только Текущая дата сбора» новые HH и Работа.ру строки (отклики и автофит) должны получать в колонке «Дата» текущий день сбора по Москве. Дата отклика/создания резюме и выбранный исторический период не заменяют этот день. Исходные timestamps сохраняются в служебных данных; период запроса источников остаётся отдельным параметром. Это не поручение массово переписать исторические строки. Реализация: общий `utils/data_processor.py::collection_date`, HH `_lead_from_resume`; commit1a5876217. Проверено81targetedtests иorigin/RURabotaruntime. Evidence `C:/Users/admin/Desktop/Project/outputs/collection-date-20261014/EVIDENCE.md`.
