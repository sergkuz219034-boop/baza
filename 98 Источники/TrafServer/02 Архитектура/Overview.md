# Overview

Теги: #архитектура

## Что это за workspace

Текущий workspace нужен не для разработки одного изолированного сервиса, а для сопровождения группы связанных подсистем вокруг продукта TrafficHub.

Здесь есть:

- локальные SSH/debug утилиты;
- partial source mirror в `remote_files`;
- partial deployment snapshot в `remote_server_snapshot`;
- локальные state-файлы и SQLite базы;
- Obsidian wiki для накопления знаний.

## Что делает продукт

Продукт автоматизирует жизненный цикл лида:

1. сбор лидов из внешних источников;
2. локальная дедупликация и owner scoping;
3. выгрузка в Google Sheets;
4. рассылка и retry queue;
5. owner-scoped worker queue и отдельный worker container;
6. отдельный TrafficHub API для CRM-подобных сущностей и статистики;
7. отдельные auth, license и account management контуры.

## Что считать каноном

- Исходники в `remote_server_snapshot` и `remote_files`
- тесты `remote_files/tests/test_traffic_tenant_isolation.py`
- deployment файлы `docker-compose.yml` и `deploy/Caddyfile`

Старые заметки использовать только как вторичный контекст.

## Смежные страницы

- [[Product]]
- [[Architecture]]
- [[Backend]]
- [[Infrastructure]]
- [[Known Issues]]
