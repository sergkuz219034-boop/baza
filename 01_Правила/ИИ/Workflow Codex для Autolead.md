# Workflow Codex для Autolead

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
6. После нового знания обновлять wiki и синхронизировать `baza`.

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
- server repo commit/push выполнен;
- GitHub checks зелёные;
- live runtime healthy;
- wiki обновлена;
- `baza` синхронизирована.

## Связанные заметки

- [[01_Правила/ИИ/Workflow Codex для дебага и разработки]]
- [[01_Правила/ИИ/Правила для ИИ]]
- [[03_Ошибки/Отладка/Рецепт отладки]]
- [[01_Правила/Плейбуки/Fast debug loop]]
- [[02_Код/Эксплуатация/Воркеры и расписание]]
- [[02_Код/Эксплуатация/Конфигурация]]
