# 2026-06-01 import graph и полнота remote_files

Теги: #debug

## Симптом

Локальное зеркало `remote_files/traffic_hub` выглядит неполным относительно импортов в точке входа и зависимостях API.

## Зона проекта

- API / tests / remote_files
- Связанные файлы: [[traffic_hub app]], [[traffic_hub deps]], [[tenant isolation tests]]

## Текущая гипотеза

Проблема связана не только с логикой tenant isolation, но и с нарушенным import graph: часть модулей отсутствует в зеркале или не была синхронизирована.

## Проверки

### Проверка 1

- Что сделал: Сопоставил импорты из `remote_files/traffic_hub/app.py` и `remote_files/traffic_hub/api/deps.py` со списком файлов в `remote_files`.
- Что ожидал: Найти все импортируемые роутеры, сервисы, config-модули и websocket-часть в локальном зеркале.
- Что увидел: В зеркале отсутствуют несколько модулей, на которые есть прямые импорты.

### Проверка 2

- Что сделал: Прочитал тесты `test_traffic_tenant_isolation.py` и ключевые роутеры `offers.py`, `stats.py`.
- Что ожидал: Подтвердить, что тесты опираются на доступные в зеркале модули.
- Что увидел: Роутеры и тесты ссылаются на дополнительные сервисы и модули, которых локально пока не видно.

## Наблюдения

- `traffic_hub/app.py` импортирует `auth`, `finance`, `funnels`, `messengers`, `tools`, `tracking`, `traffic_hub.api.ws`.
- `traffic_hub/api/deps.py` импортирует `traffic_hub.authz`, `traffic_hub.config.settings`, `traffic_hub.external_auth`, `utils.access`.
- `traffic_hub/api/routers/stats.py` импортирует `traffic_hub.services.stats_service`.
- В текущем зеркале есть только часть этих модулей.
- SSH-доступ к серверу `150.241.70.31` подтверждён; сервер отвечает как `TrafficHub.play2go.cloud`.
- Локальная папка `_sshdeps_local` содержит некорректно импортируемый `paramiko`, поэтому часть проблем в workspace относится к инструментам диагностики, а не к удалённому проекту.
- Реальный проект на сервере существенно шире локального `remote_files`: кроме `traffic_hub/*` используются корневые `main.py`, `api/*`, `services/*`, `config/*`, `utils/*`, `docker-compose.yml`, `license_auth/*`, `AccountManager/*`.
- Прод-запуск идёт через Docker Compose. Контейнер `autolead_server_bot` жив и healthy, `license_auth` и `account_manager` запущены отдельно, перед ними стоит `caddy`.
- В `data/autolead.log` и `docker logs autolead_server_bot` видны повторные перезапуски процесса с сообщением `Получен сигнал завершения`.
- В системном журнале сервера видны регулярные brute-force попытки SSH против `root`, а также успешные password-login с текущего IP.
- В `main.py` обработчик SIGTERM/SIGHUP пишет, что ждёт завершения текущей работы, но затем сразу вызывает `sys.exit(0)`.
- `services/leads_service.py::run_server_mode()` не завершает главный цикл по `stop_event`; флаг останова влияет только на плановый job, но не на сам scheduler loop.
- `api/routers/jobs.py::_broadcast_ws()` вызывает `asyncio.get_event_loop()` из sync-кода и worker-thread'ов. Исключения проглатываются, поэтому события `job_start/job_done/job_error` могут тихо не доходить до WebSocket-клиентов.
- `api/server.py::_push_status_loop()` частично маскирует эту проблему, потому что раз в 2 секунды пушит снимок статуса, но это не заменяет событийную модель и скрывает дефект наблюдаемости.
- `utils/control_sync.start_background_sync()` защищён от двойного старта живым `_thread`, поэтому двойная инициализация из `main.py` и `api/server.py` выглядит неприятно архитектурно, но не подтверждена как текущая первопричина.
- В `api/routers/settings.py` endpoint `DELETE /db` правильно использует `bind_current_username(principal.username)`, но соседние `DELETE /db/autofit`, `/db/leads`, `/db/send-history`, `/db/invite-history`, `/db/retry-queue`, `/db/run-log` вызывают очистку без `bind_current_username`.
- `utils/database.py` в функциях `clear_*` фильтрует записи через `_owner_filter_sql()`, а при пустом current user подставляет фиктивный owner `__hidden_without_owner__`.
- Следствие: часть destructive endpoints может возвращать успешный ответ и `deleted=0`, фактически не очищая данные реального пользователя.
- В `api/routers/settings.py::_write_imported_secret_files()` импорт настроек удаляет все существующие secret-файлы, которых нет во входящем payload.
- В `docker-compose.yml` прокинуты `ACCOUNT_MANAGER_BASIC_AUTH_USER/HASH`, но в `deploy/Caddyfile` basic auth настроен только для `AI_AGENT_DOMAIN`; для `ACCOUNT_MANAGER_DOMAIN` эти переменные не используются.

## Вывод

Подтверждено, что локальный набор файлов не совпадает с реальным проектом на сервере, поэтому анализ только по `remote_files` даёт неполную картину. Дополнительно подтверждены две реальные проблемы прод-качества: небезопасный SSH-доступ по паролю для `root` и некорректный graceful shutdown в `main.py`, который может обрывать фоновые задачи вопреки заявленному поведению.
Отдельно подтверждён дефект observability/runtime: job-статусы для WebSocket отправляются из мест, где event loop может отсутствовать, а ошибка при этом подавляется. Это создаёт ложное впечатление, что backend "молчит", хотя задача реально идёт.
Подтверждён ещё один прикладной дефект: часть API очистки данных реализована непоследовательно и, вероятно, не очищает owner-scoped данные пользователя из-за отсутствия `bind_current_username()`. Также подтверждён config-risk: импорт настроек может удалить дополнительные secrets, а конфиг reverse proxy содержит неиспользуемую защиту для Account Manager.

## Следующий шаг

Проверить связанные участки кода вокруг фоновых задач, owner-scoped доступа и runtime-конфигурации, чтобы отделить уже подтверждённые проблемы от потенциальных регрессий.

## Связанные заметки

- [[traffic_hub app]]
- [[traffic_hub deps]]
- [[tenant isolation tests]]
