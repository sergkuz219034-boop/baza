# 2026-06-17 hermes workspace tabs missing

Теги: #debug #hermes #dashboard #workspace

## Симптом

На `am.traffic-hubcrm.ru/hermes/chat/new` виден упрощённый экран Victoria recruiter с вкладками только `Чат`, `Память / Obsidian`, `Статус`. Пользователь ожидает интерфейс ближе к `outsourc-e/hermes-workspace` с большим числом разделов.

## Гипотеза

Сейчас открыт не upstream `hermes-workspace`, а локальный fallback dashboard, который специально урезан до трёх навигационных пунктов.

## Проверка

- В `tools/hermes_fallback_dashboard.py` навигация жёстко определена как `Чат`, `Память / Obsidian`, `Статус`.
- Тот же файл рендерит только три режима: `renderChat()`, `renderMemory()`, `renderStatus()`.
- В `docs/deployment.md` прямо зафиксировано, что публичный `/hermes/` временно обслуживает `hermes-fallback-dashboard.service` на `:3000`, а не upstream `outsourc-e/hermes-workspace`.
- В `remote_server_snapshot/AccountManager/dashboard/index.html` вкладка Hermes ведёт на внешний `https://am.traffic-hubcrm.ru/hermes/`, но не содержит собственного полного SPA Hermes Workspace.

## Наблюдение

Ожидаемые вкладки из upstream репозитория — например Chat, Sessions, Memory, Skills, Terminal, Jobs, MCP, Dashboard, Agent View, Operations — относятся к другому приложению и другому развёртыванию. Локальный fallback намеренно не пытается их воспроизвести.

## Вывод

Отсутствие остальных вкладок здесь не баг рендера, а результат выбранного fallback-контура. Чтобы вернуть полный интерфейс, нужно поднимать именно `hermes-workspace` вместо fallback dashboard и отдельно проверить reverse proxy / base path.

## Следующий шаг

Сверить live deployment c `outsourc-e/hermes-workspace` и решить, нужен ли полный swap fallback -> upstream или достаточно оставить упрощённый dashboard как стабилизационный режим.
