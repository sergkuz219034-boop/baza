# Hermes workspace tab entrypoint

## Проблема

Hermes-вкладка в AccountManager показывала устаревший репозиторий `fathah/hermes-desktop` и не давала нормальный путь к актуальному Workspace.

## Контекст

- AccountManager рендерит Hermes-карточку из `GET /api/dashboard/hermes/repo-info`.
- Пользователю нужен быстрый вход в Hermes Workspace прямо из AccountManager, а не отдельный perimeter с дополнительной basic-auth ступенью.
- Self-hosted `hermes-workspace` на live-сервере уже может публиковаться через reverse proxy на `:3000`.

## Решение

- Перевести Hermes repo-info на `outsourc-e/hermes-workspace`.
- Поднять server-side `hermes-workspace` на `:3000`.
- Добавить явный entrypoint `/hermes` на `am.traffic-hubcrm.ru`.
- Публиковать `/hermes` через `handle`, а не `handle_path`, чтобы reverse proxy не срезал base path у Vite UI.
- В sidebar-вкладке Hermes (`data-tab="ai-agent"`) сделать прямой переход на `/hermes/`.

## Последствия

- AccountManager показывает актуальный repo / release / screenshots по Workspace.
- Переход на Workspace идёт через тот же домен, где уже живёт UI AccountManager.
- `ai.traffic-hubcrm.ru` остаётся отдельным AI perimeter и не мешает открытию Hermes-вкладки из менеджерского интерфейса.
- Repo-card может оставаться вспомогательным экраном в коде, но основной пользовательский сценарий больше через него не проходит.

## Альтернативы

- Публиковать Workspace через `ai.traffic-hubcrm.ru/hermes` и заставлять оператора проходить отдельный basic-auth.
- Поднять Workspace на отдельном поддомене.
- Оставить внешний GitHub/website link без server-side redirect.
