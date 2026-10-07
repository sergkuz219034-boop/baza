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
