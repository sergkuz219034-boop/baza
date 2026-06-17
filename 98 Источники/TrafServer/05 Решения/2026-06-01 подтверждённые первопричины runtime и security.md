# 2026-06-01 подтверждённые первопричины runtime и security

## Контекст

Анализ выполнен по живому серверу `/root/TrafficHub`, системным журналам, `docker-compose.yml`, `main.py`, `api/server.py`, `api/routers/jobs.py`, `services/leads_service.py`, `api/autolead_access.py`, `api/ws_manager.py`.

## Подтверждённые выводы

### 1. Root SSH по паролю — критическая проблема окружения

- `root` доступен по паролю извне.
- В локальных root-утилитах пароль сохранён в открытом виде.
- В `journalctl` видны массовые brute-force попытки по `sshd`.

Вывод:

Это не просто "неидеальная настройка", а подтверждённая первопричина высокого риска компрометации прод-сервера.

### 2. Graceful shutdown в `main.py` декларативный, но не фактический

- Обработчик сигнала пишет, что ждёт завершения текущей работы.
- После `stop_event.set()` код сразу делает `sys.exit(0)`.
- Планировщик запущен как `daemon=True`.
- `run_server_mode()` не выходит из главного цикла по `stop_event`.

Вывод:

Остановка процесса сейчас не является корректным graceful shutdown. На рестарте возможен жёсткий обрыв фоновой работы и частично выполненных операций.

### 3. WebSocket-события job-статуса ненадёжны

- `api/routers/jobs.py::_broadcast_ws()` вызывается из sync-роутов и worker-thread'ов.
- Внутри используется `asyncio.get_event_loop()`.
- Исключения проглатываются.
- Периодический `_push_status_loop()` в `api/server.py` маскирует проблему snapshot-пушем раз в 2 секунды.

Вывод:

Событийная доставка статусов `job_start/job_done/job_error/job_stop` не гарантирована. Это дефект observability и UX, а не просто "косметика".

### 4. Локальный `remote_files` нельзя считать полным source of truth

- На сервере проект шире локального зеркала.
- Анализ только по `remote_files` может создавать ложные гипотезы о сломанных импортах и отсутствующих модулях.

Вывод:

Для расследований этого проекта source of truth — серверный `/root/TrafficHub` или синхронизированный snapshot, а не текущий фрагмент `remote_files`.

### 5. Часть API очистки данных даёт ложный успех

- `DELETE /db` использует `bind_current_username(principal.username)`.
- Соседние endpoints очистки таблиц (`/db/leads`, `/db/send-history`, `/db/retry-queue`, `/db/run-log`, `/db/autofit`, `/db/invite-history`) этого не делают.
- Внутренние функции `utils.database.clear_*()` зависят от `get_current_username()`.
- При пустом user context фильтр переключается на фиктивный owner `__hidden_without_owner__`.

Вывод:

API может отвечать `ok`, но ничего не удалять для реального пользователя. Это подтверждённый прикладной дефект, а не просто stylistic issue.

### 6. Импорт settings/secrets может удалить лишние секреты

- `_write_imported_secret_files()` удаляет все существующие exportable secret-файлы, которых нет в импортируемом payload.
- Это поведение не выглядит ограниченным только legacy-файлами и затрагивает весь `secrets/`.

Вывод:

Частичный или устаревший import-bundle способен снести дополнительные секреты и вызвать скрытую деградацию auth/runtime-конфигурации.

### 7. Reverse proxy содержит security drift

- В `docker-compose.yml` есть переменные `ACCOUNT_MANAGER_BASIC_AUTH_USER/HASH`.
- В `deploy/Caddyfile` basic auth реально применяется только к `AI_AGENT_DOMAIN`.
- Для `ACCOUNT_MANAGER_DOMAIN` reverse proxy открыт без использования этих переменных.

Вывод:

Имеется рассинхрон между ожидаемой и фактической защитой периметра. Даже если у Account Manager есть собственная JWT-проверка, конфиг вводит в заблуждение и повышает риск ошибочного ощущения защищённости.

### 8. Account Manager использует жёстко заданный дефолтный JWT-secret

- В `docker-compose.yml` для `account_manager` задан дефолтный `SESSION_SECRET_KEY`.
- Значение выглядит статическим и общим, а не уникальным для конкретной инсталляции.
- `AccountManager/api/main.py` проверяет bearer/cookie token именно этим secret.

Вывод:

Если инсталляция работает на дефолтном значении, любой знающий этот ключ может подписать admin JWT и получить доступ к Account Manager.

### 9. В Account Manager есть fail-open ветка при отсутствии secret

- В `AccountManager/api/main.py` внутри `auth_middleware` есть логика:
  `if not secret: return await call_next(request)`.
- Это bypass всей проверки токена, если переменная окружения не задана.

Вывод:

Сейчас в docker-compose это частично маскируется дефолтным secret, но сама конструкция опасна: при конфигурационном drift или альтернативном запуске middleware становится fail-open вместо fail-closed.

## Безопасный вектор исправления

1. Убрать `root` password login и вынести SSH-secrets из кода.
2. Переделать shutdown lifecycle: stop signal, join worker-thread, явный выход scheduler loop.
3. Хранить event loop для WS-статусов явно и не глотать ошибки бесследно.
4. Починить owner binding в destructive settings-endpoints.
5. Сделать импорт secrets неразрушающим для посторонних файлов или явно ограничить список управляемых файлов.
6. Убрать дефолтный JWT-secret у Account Manager и перевести auth на fail-closed поведение.
7. Синхронизировать локальный snapshot проекта перед следующими точечными фиксами.
