# TrafficHub Partner Integrations

## Назначение
Хранит настройки партнёрских сетей TrafficHub и postback URL для приёма конверсий.

## Подтверждённые сети
- LeadSU: API token + postback URL.
- Lovko: email/password для синхронизации офферов и финансов.
- Пампаду: только postback URL, без API token.

## Runtime-факты
- Основной UI: `dashboard/app.js`.
- Старый TrafficHub UI: `dashboard/traffic/index.html`.
- API: `traffic_hub/api/routers/integrations.py`.
- Postback endpoint: `traffic_hub/api/routers/postbacks.py`.

## Правило
Пампаду нельзя валидировать по `credentials.token`: в текущей интеграции token отсутствует. Настроенность Пампаду определяется по сгенерированному postback URL.
