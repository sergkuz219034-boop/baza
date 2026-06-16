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

- [[материалы/документы/TrafficHub-obsidian/04-Database/Schema|Схема БД]]
- [[материалы/документы/TrafficHub-obsidian/06-Deployment/Docker|Docker]]
