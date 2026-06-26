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

## Remote offers

- `GET /traffic-api/settings/integrations/leadsu/offers` возвращает remote LeadSU offers по owner-scoped token.
- `GET /traffic-api/settings/integrations/lovko/offers` возвращает remote Lovko offers по owner-scoped email/password.
- LeadSU sync перед импортом конверсий подтягивает offers и связывает `conversions.offer_id` с локальной `offers.id`.
- Если control store недоступен в degraded/test контуре, чтение user integration settings должно падать в `{}`, а не валить API.

## Проверка

- Commit `3fd3f611b`.
- Container tests: `tests/test_integrations_sync.py`, `tests/test_integrations_partner_api.py`, `tests/test_traffic_tenant_isolation.py` → `19 passed`.
