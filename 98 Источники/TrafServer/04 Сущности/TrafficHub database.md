# TrafficHub database

Теги: #сущность

## Тип

Модуль / схема БД

## Где находится

`remote_files/traffic_hub/models/database.py`

## Роль в системе

Описывает business entities TrafficHub и async DB access layer. Именно здесь видно, какие сущности реально поддерживает `/traffic-api/*`.

## Входы

- SQLAlchemy session
- settings.database_url

## Выходы

- async engine
- ORM models

## Зависимости

- [[Multi-Tenant]]
- [[TrafficHub app]]

## Типовые сбои или риски

- dev/prod divergence между SQLite и PostgreSQL;
- сложность миграций tenant hardening.
