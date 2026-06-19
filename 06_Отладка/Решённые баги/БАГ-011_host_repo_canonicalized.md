# БАГ-011: live работал из mutable checkout внутри контейнера

## Симптом

Фактические live-правки существовали в `/app` внутри `autolead_server_bot`, а не в host-side репозитории. Это позволяло runtime и каноническому коду расходиться.

## Зона системы

- `/root/TrafficHub`
- `/app` внутри `autolead_server_bot`
- `docker compose`
- image build pipeline для `autolead_bot`, `worker`, `license_auth`, `license_server`, `account_manager`

## Гипотеза

Нужно сделать `/root/TrafficHub` единственным каноническим checkout на сервере и собирать контейнеры только из него. `/app` должен быть лишь результатом `docker build`, а не местом ручной жизни кода.

## Проверка

- Проверен `docker inspect autolead_server_bot`: bind-монтируются только `data/*` и `secrets`, но не исходники `/app`.
- В `/root/TrafficHub` найден полноценный git checkout с `docker-compose.yml`, `.env` и remote `origin`.
- Текущий live-state из `/app` синхронизирован в `/root/TrafficHub`.
- Из `/root/TrafficHub` выполнены `docker compose build` и `docker compose up -d --force-recreate`.
- После пересборки commit в `/root/TrafficHub` и commit внутри нового `/app` совпали: `fcb7efdf389094374fa53015ae7b4ba72fd1e88a`.

## Наблюдение

Серверный канон теперь выглядит так:

- source of truth на сервере: `/root/TrafficHub`
- runtime data / secrets: `/root/TrafficHub/data/*`, `/root/TrafficHub/secrets`
- `/app` в контейнере: только build artifact из host checkout

Дополнительно:

- предыдущий dirty-state сохранён в backup-ветке `backup-pre-host-canonical-20260618`
- синхронизированный канонический state сохранён в `main` commit `fcb7efdf`

## Вывод

Канонический workflow для live:

- менять код в `/root/TrafficHub`
- коммитить в git checkout на host
- пересобирать контейнеры через `docker compose` из `/root/TrafficHub`
- не считать `/app` источником истины

## Следующий шаг

- синхронизировать `main` с GitHub remote, чтобы server canonical и GitHub canonical не расходились;
- при необходимости запретить ручные hotfix-правки в `/app` операционно, а не только договорённостью.
