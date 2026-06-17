# TrafServer Workspace Index

Это не каноническая база знаний. Канон теперь в [baza](C:/Users/Арт/Desktop/bazaGIT/baza).

Этот vault оставлен как source workspace для исследований TrafServer / TrafficHub, серверных процедур и промежуточных заметок.

## Быстрый старт

1. Для новой проблемы открывай [[01 Расследования/README|раздел расследований]].
2. Для устойчивой картины системы смотри [[02 Архитектура/README|архитектуру]].
3. Для повторяемых действий используй [[03 Плейбуки/README|плейбуки]].
4. Для конкретных модулей и файлов открывай [[04 Сущности/README|сущности]].
5. Для подтверждённых выводов и trade-off смотри [[05 Решения/README|решения]].

## Основные разделы

### Расследования

- [[01 Расследования/2026-06-12 hermes deploy and telegram user bridge|Hermes deploy и Telegram bridge]]
- [[01 Расследования/2026-06-10 user settings use per-user Rabota auth|Per-user Rabota auth]]
- [[01 Расследования/2026-06-08 tenant isolation логов и Google Sheets|Tenant isolation логов и Google Sheets]]

### Архитектура

- [[02 Архитектура/Overview|Общий обзор]]
- [[02 Архитектура/Authentication|Аутентификация]]
- [[02 Архитектура/Authorization|Авторизация]]
- [[02 Архитектура/Multi-Tenant|Multi-tenant модель]]
- [[02 Архитектура/Database|База данных]]
- [[02 Архитектура/Deployment|Деплой]]

### Плейбуки

- [[03 Плейбуки/Debugging|Дебаг]]
- [[03 Плейбуки/Server-only development|Server-only development]]
- [[03 Плейбуки/Server repo push to GitHub|Push с сервера в GitHub]]
- [[03 Плейбуки/Documentation synchronization contract|Контракт синхронизации документации]]

### Сущности

- [[04 Сущности/TrafficHub app|TrafficHub app]]
- [[04 Сущности/TrafficHub database|TrafficHub database]]
- [[04 Сущности/Autolead runtime|Autolead runtime]]
- [[04 Сущности/Control store|Control store]]

### Решения

- [[05 Решения/2026-06-01 architecture map current server|Карта архитектуры текущего сервера]]
- [[05 Решения/2026-06-01 db and api inventory current sources|Инвентарь БД и API]]
- [[05 Решения/2026-06-01 env ownership map|Карта ownership и env]]

## Вне wiki

- `tools/` — SSH и remote helper scripts
- `remote_files/` — read-only зеркало удалённого кода
- `remote_server_snapshot/` — snapshots окружения
- `docs/` — вспомогательные документы

## Канон

- живой сервер и контейнеры;
- `/root/TrafficHub` на сервере;
- GitHub как удалённая история;
- этот vault как инженерная карта.
