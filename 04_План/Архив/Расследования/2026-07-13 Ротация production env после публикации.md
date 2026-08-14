# Ротация production env после публикации

## Симптом

Содержимое production `.env` было опубликовано. Все внутренние shared secrets и внешние credentials из файла считаются скомпрометированными.

## Зона системы

- production checkout `/root/TrafficHub`
- `.env`, `docker-compose.yml`
- контейнеры `traffichub_app`, `traffichub_worker`, `traffichub_account_manager`, `traffichub_license_auth`, `traffichub_license_server`, `traffichub_standalone_content_bot`, `traffichub_hr_ai_worker`, `traffichub_postgres`, `traffichub_redis`
- PostgreSQL role/database `traffichub`
- `license_server/app.py`
- `hr_ai_worker/main.py`
- `hr_ai_worker/init_db.py`

## Гипотеза

1. Внутренние secrets можно безопасно заменить локально.
2. Внешние API credentials нельзя генерировать в Codex, их нужно перевыпустить у провайдеров.
3. Перед recreate нужно восстановить валидность compose, потому что `.env` не содержал обязательные DB-переменные.

## Проверка

- `traffichub-live` не сработал из-за устаревшего локального пути ключа; использован рабочий alias `traffichub-live-artem`.
- До изменений live-сервисы были healthy, но `docker compose ps/config` падал: `DATABASE_URL` отсутствовал.
- `.env` до ротации: `root:docker 640`; backup создан как `.env.backup.secret-rotation-20260713104017`, `root:root 600`, Git-ignore подтверждён.
- В `.env` отсутствовали `DATABASE_URL`, `ACCOUNT_MANAGER_DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_PASSWORD`.
- `OPENROUTER_API_KEY` был пустым в `.env`, но требовался `hr_ai_worker`; текущий runtime key перенесён из запущенного контейнера без вывода значения, чтобы восстановить compose до ручной ротации OpenRouter.

## Наблюдение

- Сгенерированы новые локальные значения для `SESSION_SECRET_KEY`, `LICENSE_API_KEY`, `CONTENT_BOT_SHARED_KEY`, `HERMES_DASHBOARD_BASIC_AUTH_SECRET`, `POSTGRES_PASSWORD`.
- Пароль существующей PostgreSQL role `traffichub` изменён через SQL; schema, grants, owners, volume и данные не менялись.
- Добавлены согласованные `DATABASE_URL` и `ACCOUNT_MANAGER_DATABASE_URL`.
- После recreate основной API, worker, AccountManager, License Auth, License Server, standalone content bot, PostgreSQL и Redis прошли health.
- `license_server` и `hr_ai_worker` падали на `postgresql+asyncpg://`, потому что используют sync-драйверы. В production checkout добавлена нормализация DSN в sync-compatible `postgresql://`.
- `hr_ai_worker` после исправления DSN не нашёл `session_string` Виктории в таблице `telegram_accounts`; таблица существует, но пуста. Worker переведён в idle mode вместо restart-loop.

## Вывод

- Локальная часть ротации выполнена без вывода секретов.
- Production `.env` после проверки ужесточён до `root:root 600`.
- Backup `.env` оставлен для ручного контроля и отката.
- Внешние credentials всё ещё требуют ручного перевыпуска у провайдеров: Telegram, LeadSU, Lovko, DeepSeek, FreeLM, CloseRouter, OpenRouter и открытые Basic Auth passwords.
- В checkout остались незакоммиченные hotfix-изменения в `license_server/app.py`, `hr_ai_worker/main.py`, `hr_ai_worker/init_db.py`; commit/push не выполнялись из-за требования инцидентного задания.

## Следующий шаг

- Перевыпустить внешние credentials в кабинетах провайдеров и заменить их через безопасный интерактивный ввод на сервере, не через чат.
- Решить, нужен ли `hr_ai_worker` как Telethon user-session worker. Если нужен, восстановить `telegram_accounts.session_string`; если не нужен, удалить/отключить сервис из compose как legacy.
- Закрепить DSN-нормализацию в product commit после окончания запрета на commit/push.

Связано: [[99_Архив/Решения/Production env хранится как root-only secret]]
