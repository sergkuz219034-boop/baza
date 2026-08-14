# 2026-06-30 Hermes removal keep Telegram HR Agent

## Симптом

Пользователь попросил удалить Hermes и оставить только Telegram HR Agent.

## Зона системы

- live repo: `/root/TrafficHub`
- compose: `docker-compose.yml`
- reverse proxy: `deploy/Caddyfile`, `deploy/Caddyfile.http`
- AccountManager UI: `AccountManager/dashboard/index.html`, `AccountManager/dashboard/app.js`, `AccountManager/dashboard/style.css`
- AccountManager API: `AccountManager/api/routers/dashboard.py`
- runtime container: `traffichub_hermes`

## Гипотеза

Hermes был отдельным runtime-сервисом и UI-вкладкой AccountManager. Telegram HR Agent живёт отдельно в AccountManager/API и не должен удаляться вместе с Hermes.

## Проверка

- `docker compose config --services` после правки больше не содержит `hermes`.
- `rg -n 'hermes|HERMES|ai-agent|AI_AGENT' docker-compose.yml deploy .github AccountManager/api AccountManager/dashboard README.md` не нашёл активных ссылок.
- `docker rm -f traffichub_hermes` удалил orphan-контейнер.
- `docker exec traffichub_caddy caddy validate --config /etc/caddy/Caddyfile` прошёл.
- `docker exec traffichub_caddy caddy reload --config /etc/caddy/Caddyfile` применил новый Caddyfile.
- `python3 -m pytest -q` в `/root/TrafficHub`: `419 passed, 43 skipped`.
- `/api/health` на live вернул `status=ok`, `control.backend=postgres`.

## Наблюдение

Hermes был связан с системой через:

- сервис `hermes` в `docker-compose.yml`;
- public route `/hermes*` и `am.*` reverse proxy surface в Caddy;
- вкладку `ИИ Агент -> Hermes` в AccountManager;
- API `/api/dashboard/hermes/repo-info`;
- CI env-переменные `HERMES_DASHBOARD_*`;
- runtime-контейнер `traffichub_hermes`.

Telegram HR Agent использует другой контур:

- `traffic_hub/api/routers/hr_agent.py`;
- `traffic_hub/hr_agent/service.py`;
- UI-вкладка `data-tab="hr-agent"`;
- endpoints `/api/hr-agent/telegram/*`.

## Вывод

Hermes удалён из production stack. Telegram HR Agent оставлен как единственный AI-agent контур в AccountManager.

Канонический текущий факт: в compose не должно быть сервиса `hermes`, а live `docker ps -a` не должен показывать `traffichub_hermes`.

## Следующий шаг

- Если понадобится новый AI-agent UI, добавлять его как отдельный явно названный продуктовый модуль, а не возвращать Hermes routes.
- Старые wiki-записи про Hermes считать историей, если они противоречат этой записи и текущему live compose.
