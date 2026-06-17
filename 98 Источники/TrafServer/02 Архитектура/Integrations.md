# Integrations

Теги: #архитектура

## Подтверждённые интеграции

- `Rabota.ru` — сбор лидов, сообщения, OAuth token exchange
- `Google Sheets` — pending/processed spreadsheets, service account upload
- `SuperJob` — отдельный scraper через AdsPower-параметры
- `Leadsu` и `Lovko` — TrafficHub network integrations
- `AccountManager` — отдельный сервис, связанный через compose и домен
- `Hermes Agent` — внешний runtime с отдельным container-based deployment и Telegram user-session bridge для личного аккаунта; bridge подмешивает recruiting prompt, routing brief и retrieval по отдельному vault Виктории, а ответ генерируется через `run_agent.AIAgent`; см. `tools/hermes_telegram_user_bridge.py` и архив `hermes_project.zip`

## Почему интеграции распределены

- operational integrations живут в runtime;
- business/network integrations живут в TrafficHub;
- auth и account tooling вынесены в отдельные сервисы.
- Hermes здесь не встроенный backend-модуль, а отдельный runtime perimeter: контейнер поднимает gateway, а Telegram-личка требует отдельного Telethon bridge, session storage и доступа к Obsidian vault для context retrieval.

## Смежные страницы

- [[API]]
- [[Security]]
