# Deployment

Теги: #архитектура

## Источник истины

- `remote_server_snapshot/docker-compose.yml`
- `deploy/Caddyfile`

## Как разворачивается система

1. Собираются контейнеры приложения и AccountManager.
2. Поднимаются `autolead_bot`, `worker`, `postgres`, `redis`, `license_auth`, `license_server`, `account_manager`.
3. Caddy публикует наружу web/auth/account-manager контуры.
4. Состояние хранится в разделённых mounted volumes.

## Hermes runtime

Hermes не является частью core TrafficHub deployment, но существует как отдельный container/runtime perimeter:

- `docker-compose.yml` из `hermes_project.zip` поднимает `nousresearch/hermes-agent:latest` через `gateway run`;
- `hermes-home` выступает как отдельный `HERMES_HOME` volume;
- Telegram personal-account bridge делается отдельным скриптом на Telethon, а не через bot token;
- текущий bridge подмешивает recruiting prompt, routing brief и Obsidian-context перед вызовом Hermes runtime.
- В live server deployment bridge сейчас запущен под `codex`, а отдельный recruiter-vault лежит в `/home/codex/obsidian/hermes-victoria-vault`.
- Генерация ответа идёт через `run_agent.AIAgent` из `/usr/local/lib/hermes-agent`; bridge не должен опираться на общий старый export как основной knowledge source.
- Публичная точка входа Hermes Workspace теперь публикуется через `am.traffic-hubcrm.ru/hermes` и идёт через тот же reverse-proxy контур, что и AccountManager.
- Для Hermes Workspace добавлен отдельный server-side OpenAI-compatible gateway `victoria-recruiter-gateway.service` на `127.0.0.1:8642`.
- Этот gateway не отправляет сообщения в Telegram; он нужен для dashboard/chat внутри Workspace и вызывает тот же recruiter brain из `/home/codex/hermes-user-bridge/hermes_telegram_user_bridge.py` с vault `/home/codex/obsidian/hermes-victoria-vault`.

## Сети

- `core_net` — внутренняя сервисная сеть
- `edge_net` — reverse-proxy и публичные upstream

Отдельная `account_manager_net` была удалена как лишняя.

## Storage layout

- `data/runtime/` — SQLite/runtime-состояние
- `data/runtime/secrets/` — runtime-кэши приложения
- `data/logs/` — логи
- `data/debug/` — debug-артефакты
- `data/backups/` — backup-артефакты
- `secrets/` — системные ключи и identity-файлы установки

## Что важно для запуска

- `SESSION_SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `DB_PATH`
- `CONTROL_DB_PATH`
- `RUNTIME_DATA_DIR`
- `RUNTIME_SECRETS_DIR`
- `CONFIG_FILE`
- `TOKEN_FILE`
- `GS_SERVICE_ACCOUNT_FILE`
- `AUTH_MODE`
- `EXTERNAL_AUTH_*`
- `LICENSE_AUTH_*`
- `ACCOUNT_MANAGER_*`
- `PUBLIC_BASE_URL`

## Ограничение

По текущему workspace нельзя гарантировать полный локальный запуск всех подсистем: snapshot неполный.

## Operational note

- `worker` теперь имеет heartbeat-healthcheck;
- `worker` использует системный `secrets/` только read-only;
- runtime-secrets уже вынесены из системного `secrets/`, поэтому документы со старой моделью `./data + ./secrets` нужно считать устаревшими.
- Hermes bridge-код из архива ориентирован на отдельный runtime host; в live-контуре пришлось отдельно решить, что `run_agent` рабочий, а прямой `hermes` entrypoint нет.
- Для `codex`-запуска session sqlite должна быть writable этим пользователем, иначе Telethon падает на `readonly database`.
- Для live-recruiting режима дополнительно появились переменные:
  - `HERMES_BACKEND=runtime`
  - `HERMES_RUNTIME_PATH=/usr/local/lib/hermes-agent`
  - `HERMES_BASE_URL=http://127.0.0.1:3001/v1`
  - `REPLY_DELAY_SECONDS`
  - `REPLY_DELAY_JITTER_SECONDS`
- Workspace UI использует:
  - `HERMES_API_URL=http://127.0.0.1:8642`
  - `CLAUDE_API_URL=http://127.0.0.1:8642`
  - systemd unit `victoria-recruiter-gateway.service`

## Смежные страницы

- [[Infrastructure]]
- [[Known Issues]]
