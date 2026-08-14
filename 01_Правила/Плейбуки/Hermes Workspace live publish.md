# Hermes Workspace live publish

Теги: #плейбук

> Статус на 2026-06-26: legacy-плейбук для старого `hermes-workspace.service` на `:3000`.
> Для подключения Hermes Desktop использовать актуальную сущность [[Hermes remote gateway container]] и URL `https://traffic-hubcrm.ru/hermes`.

## Когда использовать

Когда вкладка `Hermes` в AccountManager открывается, но сам Workspace не грузится, уходит в auth-чужой perimeter или попадает в redirect-loop на `/hermes/`.

## Что нужно заранее

- SSH-доступ на live-сервер `150.241.70.31`
- Рабочий checkout `/root/TrafficHub`
- Клон `/root/hermes-workspace`
- Понимание, что `hermes-workspace` публикуется как отдельный UI на `:3000`, а не из контейнера `account_manager`
- Gateway для recruiter brain: `/home/codex/hermes-user-bridge/recruiter_workspace_gateway.py`
- Аварийный fallback UI: `/home/codex/hermes-user-bridge/hermes_fallback_dashboard.py`
- Runtime home для Workspace: `/home/codex/hermes-workspace-home`
- Recruiter Obsidian vault: `/home/codex/obsidian/hermes-victoria-vault`

## Шаги

1. Проверить, что `victoria-recruiter-gateway.service` активен и слушает `127.0.0.1:8642`.
2. Проверить, что `/home/codex/hermes-workspace-home/memory` является symlink на `/home/codex/obsidian/hermes-victoria-vault`.
3. Поднимать UI через `hermes-workspace.service`, а не вручную через shell. Unit запускает `/usr/local/bin/node ./node_modules/vite/bin/vite.js dev --host 0.0.0.0 --port 3000 --strictPort`.
4. В unit должны быть env: `HERMES_HOME=/home/codex/hermes-workspace-home`, `HERMES_API_URL=http://127.0.0.1:8642`, `CLAUDE_API_URL=http://127.0.0.1:8642`, `HERMES_WORKSPACE_AUTO_START_AGENT=false`.
5. Убедиться, что локальный health-check `http://127.0.0.1:3000/api/healthcheck` отвечает `200`.
6. В `deploy/Caddyfile` публиковать Workspace под `{$ACCOUNT_MANAGER_DOMAIN:am.traffic-hubcrm.ru}` так: `/hermes` и `/hermes/` редиректят на штатный root route `/chat/new`.
6. Не считать `/hermes/chat/new` целевым рабочим URL для текущей версии `outsourc-e/hermes-workspace`: в live dev-runtime он после гидрации уходит во внутренний TanStack Router `404`.
7. Для текущей live-сети рабочий upstream из `traffichub_caddy` — `172.22.0.1:3000`.
8. Для `/hermes/api*` в Caddy нужен `uri strip_prefix /hermes`, потому что route files Workspace живут на `/api/*`, а не на `/hermes/api/*`.
9. Для absolute static/dev-вызовов Workspace добавить Caddy proxy root paths `/claude-*`, `/cover.*`, `/manifest.json`, `/sw.js`, `/assets*`, `/src*`, `/@vite*`, `/@react-refresh*`, `/@tanstack-start*`, `/@id*`, `/@fs*`, `/__vite*`, `/node_modules*` и аналогичных на `172.22.0.1:3000`.
10. Для absolute API-вызовов Workspace добавить Caddy routes `/api/auth-check`, `/api/provider-usage`, `/api/session-status`, `/api/context-usage`, `/api/models`, `/api/memory*`, `/api/claude-proxy*`, `/api/claude-config`, `/api/update*`, `/api/network-url`, `/api/profiles*`, `/api/model*`, `/api/gateway*`, `/api/hermes-config`, `/api/runs*`, `/api/events`, `/api/cli-agents`, `/api/terminal*`, `/avatars*` на `172.22.0.1:3000` без rewrite в `/hermes`.
11. Если `/src/styles.css` отдаётся как `text/javascript`, убрать `styles.css?url` из SSR `<link rel="stylesheet">` и импортировать CSS как модуль `import '../styles.css'`.
11. Обновить `dashboard_url` в `AccountManager/api/routers/dashboard.py` на `https://am.traffic-hubcrm.ru/hermes/`.
12. В `AccountManager/dashboard/app.js` обработчик вкладок должен переводить `data-tab="ai-agent"` на `/hermes/`.
13. После изменения `app.js` обновить cache-buster в `AccountManager/dashboard/index.html`.
14. Поднять `victoria-recruiter-gateway.service`; он должен слушать `127.0.0.1:8642`.
15. Перезагрузить Caddy через `docker exec traffichub_caddy caddy reload --config /etc/caddy/Caddyfile`.

## Ожидаемые сигналы

- `https://am.traffic-hubcrm.ru/hermes` отдаёт `308` на `/chat/new`, а `/chat/new` отдаёт `HTTP/2 200`
- `systemctl is-active hermes-workspace.service victoria-recruiter-gateway.service` возвращает `active`
- `systemctl is-active hermes-fallback-dashboard.service` возвращает `inactive`
- `https://am.traffic-hubcrm.ru/chat/new` открывает Workspace без внутреннего wildcard 404
- `https://am.traffic-hubcrm.ru/api/memory/list` отдаёт recruiter vault notes, включая `memory/01 Routing Rules.md`
- `https://am.traffic-hubcrm.ru/api/memory/read?path=memory/03%20Links.md` отдаёт JSON с актуальными ссылками
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
- если Workspace shell загрузился, но внутри виден `404 Страница не найдена` на `/hermes/chat/new`, не пытаться держать этот URL как канон: для текущего live-runtime использовать entrypoint `/hermes -> /chat/new`
- если в левом верхнем углу битая иконка, проверить root static rewrite `/claude-* -> /hermes{uri}`
- если HTML `/hermes` отдаётся, но экран полностью чёрный, проверить browser dev-assets: `/src/styles.css`, `/@id/virtual:tanstack-start-client-entry`, `/@vite/client`, `/node_modules/.vite/...` должны отдавать `200`, а не `401`
- если `/src/styles.css` отдаётся как `text/javascript`, убрать `styles.css?url` из SSR `<link rel="stylesheet">` и импортировать CSS как модуль `import '../styles.css'`
- если Vite/TanStack Start слушает порт, но любые `/hermes/*` запросы уходят в timeout, не держать публичный `/hermes/` в 502: остановить Vite-процессы и включить `hermes-fallback-dashboard.service`

## Fallback dashboard

Использовать только как аварийный live-stability режим, когда upstream `outsourc-e/hermes-workspace` зависает. В штатном состоянии на 18 июня 2026 fallback выключен.

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
