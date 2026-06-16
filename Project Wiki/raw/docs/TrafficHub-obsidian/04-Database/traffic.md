# traffic_dashboard.db

## Назначение

Основная БД для **TrafficHub CRM** — модуля постбэков, воронок, финансов.

## Технологии

- **SQLAlchemy 2.0** (async)
- **Alembic** миграции

## Модели (SQLAlchemy)

Включает модели для:
- Users (JWT + 2FA)
- Funnels (воронки)
- Finance (финансы)
- Postbacks (трекинг)
- Offers
- Messengers (Telegram, VK)
- Integrations

## Миграции

```bash
alembic upgrade head
```

## Связанное

- [[04-Database/Schema|Схема БД]]
- [[06-Deployment/Docker|Docker]]
