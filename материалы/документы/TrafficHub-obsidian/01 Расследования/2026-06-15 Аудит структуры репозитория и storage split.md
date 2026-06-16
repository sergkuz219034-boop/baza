# 2026-06-15 Аудит структуры репозитория и storage split

## Симптом

- Структура проекта воспринималась как единый backend.
- В документации и обсуждениях смешивались legacy Autolead runtime, `traffic_hub`, `AccountManager` и control/auth слой.
- Появлялась ложная гипотеза, что migration на PostgreSQL уже завершена целиком.

## Зона системы

- `/root/TrafficHub`
- `README.md`
- `docs/architecture.md`
- `docs/deployment.md`
- `wiki/*`
- `requirements*.txt`

## Гипотеза

Проект уже перерос текущую ментальную модель “один backend + одна БД”, и без явной карты слоёв новый инженер будет снова и снова дебажить не тот контур.

## Проверка

- Выполнен live SSH-inspection дерева `/root/TrafficHub`.
- Проверены `docker-compose.yml`, `Dockerfile`, `README.md`, `docs/architecture.md`, `docs/deployment.md`.
- Проверены runtime-entrypoints и storage-модули:
  - `api/server.py`
  - `services/leads_service.py`
  - `utils/database.py`
  - `utils/control_store.py`
  - `traffic_hub/models/database.py`
  - `traffic_hub/migrations.py`
  - `AccountManager/api/main.py`

## Наблюдение

- Репозиторий подтверждён как hybrid-монорепозиторий.
- Operational Autolead runtime всё ещё использует SQLite.
- `traffic_hub` и `control_store` уже PostgreSQL-first.
- `AccountManager` живёт как отдельное приложение.
- В корне live-репозитория остаются legacy runtime-артефакты:
  - `.env`
  - `autolead.db`
  - Windows `.exe`

## Вывод

- Полная SQLite -> PostgreSQL migration не завершена.
- Главный безопасный шаг сейчас:
  - зафиксировать boundaries;
  - синхронизировать docs/wiki;
  - развести runtime/dev зависимости;
  - не делать big-bang file move и не ломать working runtime.

## Следующий шаг

- Держать в wiki отдельные постоянные страницы:
  - [[материалы/документы/TrafficHub-obsidian/02 Архитектура/Структура репозитория]]
  - [[материалы/документы/TrafficHub-obsidian/04 Сущности/Хранилища и runtime артефакты]]
  - [[материалы/документы/TrafficHub-obsidian/05 Решения/Не делать big-bang миграцию SQLite в PostgreSQL]]
