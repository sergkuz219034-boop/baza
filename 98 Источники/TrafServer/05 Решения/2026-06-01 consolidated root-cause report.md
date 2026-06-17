# 2026-06-01 consolidated root-cause report

## 1. Структура и стек

### Общая архитектура

Проект на сервере `/root/TrafficHub` состоит из нескольких подсистем:

- `main.py` — основной runtime Autolead и scheduler
- `api/server.py` — основной FastAPI Dashboard/API для Autolead
- `traffic_hub/app.py` — отдельный FastAPI-модуль TrafficHub с роутерами и WebSocket
- `license_auth/*` — отдельный auth-сервис
- `AccountManager/*` — отдельный сервис и UI для account/proxy/content management
- `deploy/Caddyfile` — reverse proxy
- `docker-compose.yml` — orchestration
- `config/*`, `utils/*`, `services/*` — конфигурация, инфраструктурные хелперы, бизнес-логика
- `data/*.db`, `secrets/*` — локальное состояние и секреты

### Стек технологий

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- SQLite / aiosqlite
- httpx
- Playwright
- Docker Compose
- Caddy

### Точки входа

- `main.py`
- `api/server.py`
- `traffic_hub/app.py`
- `license_auth.app:app`
- `AccountManager/api/main.py`

### Конфигурационные файлы

- `docker-compose.yml`
- `deploy/Caddyfile`
- `config/settings.py`
- `.env`
- `alembic.ini`
- `secrets/*`

### Зависимости

По `requirements.txt` подтверждены:

- `fastapi>=0.110.0`
- `uvicorn[standard]>=0.27.0`
- `sqlalchemy>=2.0.36`
- `aiosqlite>=0.20.0`
- `alembic>=1.14.0`
- `pydantic>=2.0.0`
- `python-jose>=3.5.0`
- `httpx>=0.28.1`
- `pytest>=8.0.0`
- `pytest-asyncio>=0.23.0`
- а также `playwright`, `gspread`, `google-auth`, `openai`, `aiohttp`, `aiogram`

## 2. Подтверждённое текущее поведение

- Контейнер `autolead_server_bot` сейчас `healthy`.
- `OOMKilled=false`, crash-loop не подтверждён.
- Повторы `Получен сигнал завершения` в приложении совпадают с внешними stop/start контейнера Docker, а не с OOM или внутренним panic.
- Локальный `remote_files` не является полным source of truth и не совпадает со всей серверной кодовой базой.

## 3. Подтверждённые первопричины

Важно: ниже смешаны две категории, которые нужно различать при чтении отчёта:

- `active now` — выглядит актуальным по текущему состоянию server snapshot / workspace
- `historical forensic` — было подтверждено раньше, но по текущему snapshot уже выглядит исправленным и важно скорее как след расследования

### RC-1. Root SSH по паролю на сервере

- Критичность: `Critical`
- Первопричина:
  - root-доступ по паролю разрешён
- Последствия:
  - высокий риск компрометации прод-сервера
  - полный захват инфраструктуры

Отдельное уточнение по текущему workspace:

- plaintext credentials были исторически зашиты в локальные утилиты, но на текущем шаге убраны из workspace-кода и локальной документации;
- локальные SSH-утилиты переведены на `TRAFSERVER_HOST`, `TRAFSERVER_USER`, `TRAFSERVER_PASSWORD` и helper `tools/local_ssh.py`;
- это снижает локальный operational risk, но не устраняет критичность серверной auth-модели.
- дополнительный operational нюанс: на текущей рабочей машине не подтверждён приватный ключ, соответствующий уже разрешённым server-side ключам в `/root/.ssh/authorized_keys`, поэтому отключение password auth без предварительного добавления нового ключа рискованно.

### RC-2. Graceful shutdown реализован некорректно

- Критичность: `High`
- Статус: `Historical forensic; по текущему snapshot выглядит исправленным`
- Файлы:
  - `main.py`
  - `services/leads_service.py`
- Первопричина:
  - `stop_event.set()` сопровождается немедленным `sys.exit(0)`
  - scheduler-thread запускается с `daemon=True`
  - scheduler loop не выходит по stop-флагу
- Последствия:
  - внешний restart контейнера приводит к грязному обрыву текущей работы

### RC-3. Статусы job через WebSocket ненадёжны

- Критичность: `Medium`
- Статус: `Mostly mitigated in current snapshot; требует интеграционной проверки`
- Файлы:
  - `api/routers/jobs.py`
  - `api/server.py`
  - `api/ws_manager.py`
- Первопричина:
  - отправка статусов из sync/thread-кода через `asyncio.get_event_loop()`
  - ошибки подавляются
- Последствия:
  - UI может не видеть `job_start/job_done/job_error`

### RC-4. Часть clear-endpoints возвращает ложный успех

- Критичность: `High`
- Статус: `Historical forensic; по текущему snapshot выглядит исправленным`
- Файлы:
  - `api/routers/settings.py`
  - `utils/database.py`
  - `utils/user_context.py`
- Первопричина:
  - owner-scoped `clear_*()` требуют установленный `current_username`
  - часть routes не использует `bind_current_username(principal.username)`
- Последствия:
  - API отвечает `ok`, но реальные данные пользователя не очищаются

### RC-5. У Account Manager статический дефолтный JWT secret

- Критичность: `High`
- Статус: `Historical forensic; по текущему snapshot выглядит исправленным`
- Файлы:
  - `docker-compose.yml`
  - `AccountManager/api/main.py`
- Первопричина:
  - `SESSION_SECRET_KEY` имеет дефолтное статическое значение
- Последствия:
  - при использовании дефолта токены можно подделывать

### RC-6. У Account Manager fail-open auth при пустом secret

- Критичность: `High`
- Статус: `Historical forensic; по текущему snapshot выглядит исправленным`
- Файл:
  - `AccountManager/api/main.py`
- Первопричина:
  - при пустом secret middleware пропускает запрос дальше
- Последствия:
  - при config drift auth может быть фактически отключён

### RC-7. Импорт настроек удаляет лишние secrets

- Критичность: `Medium`
- Статус: `Historical forensic; по текущему snapshot смягчено whitelist-логикой`
- Файл:
  - `api/routers/settings.py`
- Первопричина:
  - `_write_imported_secret_files()` удаляет все exportable secret-файлы вне import payload
- Последствия:
  - скрытая деградация auth/runtime после частичного импорта

### RC-8. Security drift в reverse proxy

- Критичность: `Low/Medium`
- Статус: `Active now`
- Файлы:
  - `docker-compose.yml`
  - `deploy/Caddyfile`
- Первопричина:
  - compose декларирует basic auth переменные для Account Manager
  - Caddy их фактически не использует
- Последствия:
  - ложное ощущение защищённости периметра

### RC-9. Прод-остановки контейнера — внешний orchestration event, не внутренний crash

- Критичность: `Medium`
- Статус: `Active diagnostic risk`
- Источник:
  - `docker.service` / `containerd` журналы
  - `.bash_history`
- Первопричина:
  - контейнер пересоздавался/перезапускался внешним действием
- Последствия:
  - можно ошибочно лечить “падение приложения”, когда проблема находится на уровне deploy/ops

## 4. Наиболее вероятные пользовательские симптомы

- “Приложение внезапно остановилось”
  - реальная причина: внешний restart контейнера + плохой shutdown path
- “Очистка данных не работает”
  - реальная причина: отсутствие owner binding в clear-endpoints
- “Статус задачи в UI завис/не обновился”
  - реальная причина: ненадёжная WS-доставка статусов
- “После импорта настроек что-то сломалось в auth/secrets”
  - реальная причина: destructive import secrets

## 5. Безопасный порядок исправлений

1. Security:
   - убрать root password login
   - убрать дефолтный JWT secret
   - перевести auth на fail-closed
2. Correctness:
   - починить owner binding в clear-endpoints
3. Runtime:
   - починить graceful shutdown
4. Observability:
   - стабилизировать WS status delivery
5. Config safety:
   - ограничить destructive import secrets
6. Perimeter clarity:
   - выровнять Caddy и compose по basic auth для Account Manager

## 6. Связанные документы

- `05 Решения/2026-06-01 implementation index.md`
- `05 Решения/2026-06-01 objective coverage audit.md`
- `01 Расследования/2026-06-01 import graph и полнота remote_files.md`
- `01 Расследования/2026-06-01 obsidian vault scan eperm.md`
- `05 Решения/2026-06-01 подтверждённые первопричины runtime и security.md`
- `05 Решения/2026-06-01 patch-plan confirmed fixes.md`
- `05 Решения/2026-06-01 revalidation current server snapshot.md`
- `05 Решения/2026-06-01 server-side ssh and proxy hardening plan.md`
- `05 Решения/2026-06-01 operational runbook key-based ssh migration.md`
- `05 Решения/2026-06-01 exact commands ssh migration.md`
- `05 Решения/2026-06-01 5-command ssh checklist.md`
- `05 Решения/2026-06-01 architecture map current server.md`
- `05 Решения/2026-06-01 operational map current deployment.md`
- `05 Решения/2026-06-01 redacted secret inventory.md`
- `05 Решения/2026-06-01 secret rotation priority plan.md`
- `05 Решения/2026-06-01 env surface separation plan.md`
- `05 Решения/2026-06-01 env ownership map.md`
- `05 Решения/2026-06-01 env separation change plan.md`
- `05 Решения/2026-06-01 env separation validation checklist.md`
- `05 Решения/2026-06-01 run status and retry queue root causes.md`
- `05 Решения/2026-06-01 offer mapping drift hypothesis confirmed by config merge.md`
- `05 Решения/2026-06-01 config save cross-user drift confirmed.md`
- `05 Решения/2026-06-01 root cause matrix current state.md`
- `05 Решения/2026-06-01 implementation roadmap by waves.md`
