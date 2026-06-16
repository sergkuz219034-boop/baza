# API

## Подтверждено

- legacy web/API слой живёт в `api/server.py`
- embedded `traffic-api` слой живёт в `traffic_hub/app.py`
- websocket endpoints подтверждены:
  - `/ws/log`
  - `/ws/status`
- health endpoint:
  - `/api/health`

## Что важно

- auth-модель гибридная: session cookie + fallback API auth;
- `/api/account-manager/token` является bridge endpoint, а не конечной точкой role gating;
- API нельзя рассматривать без owner/runtime semantics.

## Дальше

- [[04_Код/Бэкенд|Бэкенд]]
- [[материалы/документы/legacy-canonical-v1/08_API/Внутреннее API|Внутреннее API v1]]
- [[материалы/документы/legacy-canonical-v1/08_API/Внешнее API|Внешнее API v1]]
