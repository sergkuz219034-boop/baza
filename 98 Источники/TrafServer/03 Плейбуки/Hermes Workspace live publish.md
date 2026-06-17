# Hermes Workspace live publish

Теги: #плейбук

## Когда использовать

Когда вкладка `Hermes` в AccountManager открывается, но сам Workspace не грузится, уходит в auth-чужой perimeter или попадает в redirect-loop на `/hermes/`.

## Что нужно заранее

- SSH-доступ на live-сервер `150.241.70.31`
- Рабочий checkout `/root/TrafficHub`
- Клон `/root/hermes-workspace`
- Понимание, что `hermes-workspace` публикуется как отдельный UI на `:3000`, а не из контейнера `account_manager`
- Gateway для recruiter brain: `/home/codex/hermes-user-bridge/recruiter_workspace_gateway.py`
- Временный fallback UI: `/home/codex/hermes-user-bridge/hermes_fallback_dashboard.py`

## Шаги

1. Проверить, что `pnpm` доступен по абсолютному пути `/usr/local/lib/nodejs/node-v22.16.0-linux-x64/bin/pnpm`.
2. В `/root/hermes-workspace` выполнить установку зависимостей через `pnpm install`.
3. Поднять UI через `pnpm dev`, сохранив лог в `hermes-workspace-dev.log`.
4. Убедиться, что локальный health-check `http://127.0.0.1:3000/hermes/` отвечает `200`.
5. В `deploy/Caddyfile` публиковать Workspace через блок `handle /hermes*` под `{$ACCOUNT_MANAGER_DOMAIN:am.traffic-hubcrm.ru}`.
6. Не использовать `handle_path /hermes*`, потому что он срезает base path `/hermes/` у Vite UI.
7. Для текущей live-сети upstream должен быть `172.22.0.1:3000`, потому что `host.docker.internal` внутри `traffichub_caddy` резолвится в `172.17.0.1` и может висеть.
8. В Workspace bootstrap должен задаваться `window.__HERMES_WORKSPACE_BASEPATH__ = '/hermes'` для URL `/hermes` и `/hermes/...`; иначе TanStack Router считает basepath корнем и показывает wildcard 404 внутри уже загруженного UI.
9. Для absolute static-вызовов Workspace добавить Caddy rewrite из root paths `/claude-*`, `/cover.*`, `/manifest.json`, `/sw.js`, `/assets*` и аналогичных в `/hermes{uri}`.
10. Для absolute API-вызовов Workspace добавить Caddy rewrite из `/api/auth-check`, `/api/provider-usage`, `/api/session-status`, `/api/context-usage`, `/api/models`, `/api/claude-proxy*` в соответствующие `/hermes/api/...`.
11. Обновить `dashboard_url` в `AccountManager/api/routers/dashboard.py` на `https://am.traffic-hubcrm.ru/hermes/`.
12. В `AccountManager/dashboard/app.js` обработчик вкладок должен переводить `data-tab="ai-agent"` на `/hermes/`.
13. После изменения `app.js` обновить cache-buster в `AccountManager/dashboard/index.html`.
14. Поднять `victoria-recruiter-gateway.service`; он должен слушать `127.0.0.1:8642`.
15. Перезапустить `traffichub_account_manager` и `traffichub_caddy`.

## Ожидаемые сигналы

- `https://am.traffic-hubcrm.ru/hermes/` отдаёт `HTTP/2 200`
- `https://am.traffic-hubcrm.ru/hermes/chat/new` и `/hermes/chat/main` отдают `HTTP/2 200` и не показывают внутренний wildcard 404
- `https://am.traffic-hubcrm.ru/claude-avatar.webp` и `/manifest.json` отдают `200` через rewrite в Workspace
- `https://am.traffic-hubcrm.ru/api/auth-check` отдаёт `200` и `{"authenticated":true,"authRequired":false}`
- HTML начинается с `<title>Hermes Workspace</title>`
- `/static/app.js?...` содержит ветку `tab.dataset.tab === "ai-agent"` и `window.location.href = "/hermes/"`
- `get_hermes_repo_info()['dashboard_url']` внутри `traffichub_account_manager` возвращает `https://am.traffic-hubcrm.ru/hermes/`
- `https://am.traffic-hubcrm.ru/hermes/api/gateway-status` показывает `mode: portable`, `health: true`, `chatCompletions: true`, `models: true`
- `https://am.traffic-hubcrm.ru/hermes/api/claude-proxy/v1/chat/completions` возвращает ответ Виктории через `victoria-recruiter`

Негативные сигналы:

- `401 Unauthorized` на `am.traffic-hubcrm.ru/hermes/` означает, что запрос всё ещё попадает в AccountManager/API-контур, а не в отдельный Hermes route
- `302 -> /hermes/` по кругу означает, что в Caddy ошибочно стоит `handle_path`, а не `handle`
- публичный timeout при локальном `200` означает, что Caddy смотрит на неверный host gateway
- `Cannot find module ... vite.js` означает неполную или оборванную установку зависимостей
- экран onboarding внутри Workspace означает, что `127.0.0.1:8642` не слушает или Workspace ещё не перепробовал gateway
- если `/hermes/api/auth-check` работает, а экран onboarding остаётся, проверить absolute `/api/auth-check`: часть frontend-кода вызывает именно его
- если Workspace shell загрузился, но внутри виден `404 Страница не найдена`, проверить `window.__HERMES_WORKSPACE_BASEPATH__`; это router-level 404, а не HTTP 404
- если в левом верхнем углу битая иконка, проверить root static rewrite `/claude-* -> /hermes{uri}`
- если Vite/TanStack Start слушает порт, но любые `/hermes/*` запросы уходят в timeout, не держать публичный `/hermes/` в 502: остановить Vite-процессы и включить `hermes-fallback-dashboard.service`

## Fallback dashboard

Использовать только как временный live-stability режим, когда upstream `outsourc-e/hermes-workspace` зависает.

Компоненты:

- `hermes-fallback-dashboard.service` слушает `0.0.0.0:3000`
- `/hermes/chat/new` отдаёт простой чат с `victoria-recruiter`
- `/hermes/memory` показывает markdown из `/home/codex/obsidian/hermes-victoria-vault`
- `/hermes/api/claude-proxy/v1/chat/completions` проксируется в `victoria-recruiter-gateway.service` на `127.0.0.1:8642`

Проверка:

- `systemctl is-active hermes-fallback-dashboard.service`
- `curl -I https://am.traffic-hubcrm.ru/hermes/memory` должен вернуть `200`
- `curl https://am.traffic-hubcrm.ru/hermes/api/memory/list` должен вернуть recruiter vault notes
- chat completion должен вернуть модель `victoria-recruiter`

## Связанные сущности

- [[Deployment]]
- [[2026-06-16 hermes workspace tab repo swap]]
- [[2026-06-16 Hermes workspace tab redirect]]

## Связанные расследования

- [[2026-06-16 hermes workspace tab repo swap]]
