# 2026-06-16 Hermes workspace tab repo swap

## Симптом

Во вкладке Hermes в AccountManager отображался устаревший репозиторий `fathah/hermes-desktop` и кнопка вела не на нужный Workspace.

## Зона системы

- `AccountManager/api/routers/dashboard.py`
- `AccountManager/dashboard/app.js`
- `deploy/Caddyfile`

## Гипотеза

Hermes-карточка собирается из hardcoded GitHub-метаданных старого репозитория, а публичный entrypoint Workspace либо отсутствует, либо привязан к неудобному внешнему perimeter.

## Проверка

- На живом сервере `GET /api/dashboard/hermes/repo-info` возвращал метаданные `fathah/hermes-desktop`.
- В live `AccountManager` найден рендер `renderHermes()` с кнопками GitHub / Releases / Docs и старым описанием.
- В `deploy/Caddyfile` `am.traffic-hubcrm.ru` сначала не имел отдельного маршрута на Hermes Workspace.

## Наблюдение

- Источник устаревшей карточки подтверждён в `AccountManager/api/routers/dashboard.py`.
- На сервере поднят self-hosted `hermes-workspace` на `:3000`.
- Внешний путь через `ai.traffic-hubcrm.ru/hermes` оказался неудобным из-за отдельного basic-auth perimeter.
- Рабочая публикация переведена на `am.traffic-hubcrm.ru/hermes`, чтобы Workspace открывался из AccountManager без отдельного логин-шагa.
- Для Vite-base `/hermes/` подтверждено, что в Caddy нужен `handle`, а не `handle_path`; иначе возникает redirect-loop `302 -> /hermes/`.
- В контейнере Caddy `host.docker.internal` резолвится в `172.17.0.1`, но live Workspace доступен из `traffichub_edge_net` через `172.22.0.1:3000`; из-за этого публичный `/hermes/` висел до смены upstream.
- Сама вкладка AccountManager была обычным tab-panel `data-tab="ai-agent"` и продолжала показывать repo-card. Обработчик tab-click обновлён: для `ai-agent` браузер сразу уходит на `/hermes/`.
- Hermes repo-info теперь возвращает `outsourc-e/hermes-workspace` и preview-скриншоты из `docs/screenshots`.
- После публикации `/hermes/` Workspace продолжал показывать onboarding, хотя `/hermes/api/gateway-status` был здоровым. Причина: часть frontend-кода Hermes Workspace вызывает absolute endpoints `/api/auth-check`, `/api/gateway-status`, `/api/provider-usage`, `/api/claude-proxy/*`, а не `/hermes/api/...`.
- Для live-публикации добавлены отдельные Caddy routes, которые переписывают эти absolute `/api/*` вызовы в `/hermes/api/*` перед проксированием на `172.22.0.1:3000`.
- На 17 июня 2026 подтверждено runtime-проверкой: `https://am.traffic-hubcrm.ru/api/auth-check` возвращает `{"authenticated":true,"authRequired":false}`, `https://am.traffic-hubcrm.ru/api/claude-proxy/v1/models` возвращает модель `victoria-recruiter`, а chat completion через публичный `/api/claude-proxy/v1/chat/completions` отвечает от имени рекрутерского gateway.
- После этого Workspace shell загружался, но внутри показывал `404 Страница не найдена`. Это был не HTTP 404, а TanStack Router wildcard: `window.__HERMES_WORKSPACE_BASEPATH__` не задавался до запуска bundle, поэтому router матчился относительно `/`, а не `/hermes`.
- Гипотеза с bootstrap `window.__HERMES_WORKSPACE_BASEPATH__ = '/hermes'` была проверена, но удалена: правка не решила timeout `/hermes/*` и не должна считаться актуальным способом восстановления.
- Сломанная иконка Hermes в shell была отдельным static-path проявлением: root `/claude-avatar.webp` проксировался без rewrite и Vite отдавал 404. В Caddy добавлен static rewrite root assets в `/hermes{uri}`.
- 17 июня 2026 повторное расследование показало, что Vite/TanStack Start dev-server `outsourc-e/hermes-workspace` может зависать на любых `/hermes/*` запросах: порт слушает, `/` быстро отдаёт redirect/404, но `/hermes/`, `/hermes/api/auth-check`, `/hermes/api/memory/list` уходят в timeout. Одновременный запуск нескольких Vite-инстансов на одной папке усиливал проблему.
- Для восстановления публичного `/hermes/` без простоя поднят временный `hermes-fallback-dashboard.service` на `:3000`. Он отдаёт lightweight dashboard, проксирует chat completions в `victoria-recruiter-gateway.service` и читает Obsidian vault `/home/codex/obsidian/hermes-victoria-vault` напрямую.
- Runtime-проверка fallback: `https://am.traffic-hubcrm.ru/hermes/memory` отдаёт `200`, `/hermes/api/memory/list` возвращает `00 Index.md`, `01 Routing Rules.md`, `02 Vacancies/*`, а `/hermes/api/claude-proxy/v1/chat/completions` отвечает моделью `victoria-recruiter`.

## Вывод

Старая привязка к `hermes-desktop` была локальным hardcode. Отдельно подтверждено, что для user-flow внутри AccountManager нужно не только обновить repo-info, но и заменить поведение sidebar-вкладки Hermes на прямой переход в Workspace.

Дополнительный вывод: для self-hosted Hermes Workspace под subpath `/hermes/` нельзя ограничиваться проксированием `/hermes*`; нужно либо патчить frontend на base-aware API calls, либо прокидывать корневые `/api/*` routes на Workspace. На live выбран Caddy-level rewrite, потому что он минимально инвазивен к upstream `outsourc-e/hermes-workspace`.

Router-level 404 внутри уже загруженного Workspace лечится не Caddy-роутом `/hermes*`, а ранней установкой basepath для TanStack Router.

Если upstream Hermes Workspace снова зависает на `/hermes/*`, канонический временный workaround: держать публичный порт `3000` за `hermes-fallback-dashboard.service`, а upstream Vite чинить на отдельном порту без влияния на AccountManager.

## Следующий шаг

- При изменениях frontend-логики обновлять cache-buster у `/static/app.js`, иначе браузер может держать старый обработчик вкладок.
- Если в браузере после фикса остаётся onboarding, сначала делать hard refresh/очистку site data: серверные endpoints уже могут быть здоровыми, а старый JS/state продолжает показывать прежний экран.
