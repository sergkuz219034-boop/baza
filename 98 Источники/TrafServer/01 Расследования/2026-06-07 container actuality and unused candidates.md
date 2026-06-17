# 2026-06-07 container actuality and unused candidates

## Симптом

Нужно понять, какие контейнеры на сервере реально относятся к текущему стеку `TrafficHub`, а какие выглядят как посторонние или факультативные.

## Проверка

1. Снято текущее `docker ps`.
2. Сверен `docker-compose.yml` в `/root/TrafficHub`.
3. Сопоставлены имена контейнеров с сервисами из compose.

## Наблюдение

### Контейнеры, входящие в стек `TrafficHub`

- `autolead_server_bot`
- `traffichub_worker`
- `traffichub_postgres`
- `traffichub_redis`
- `traffichub_license_auth`
- `traffichub_license_server`
- `traffichub_account_manager`
- `traffichub_caddy`

### Контейнеры, которые не видны в `TrafficHub/docker-compose.yml`

- `searxng-local`
- `amnezia-xray`
- `mfo_api`

## Вывод

Для самого проекта `TrafficHub` актуален стек из 8 контейнеров выше.

`searxng-local`, `amnezia-xray` и `mfo_api` не подтверждаются текущим compose-файлом проекта и выглядят как соседние сервисы этого же хоста, а не обязательная часть `TrafficHub`.

## Практический смысл

- С `TrafficHub` можно работать точечно по отдельным контейнерам.
- Обычно безопасно отдельно пересобирать:
  - `autolead_server_bot`
  - `traffichub_worker`
  - `traffichub_account_manager`
  - `traffichub_license_auth`
  - `traffichub_license_server`
- `traffichub_postgres` и `traffichub_redis` не стоит трогать без причины.
- `traffichub_caddy` нужен только при изменениях маршрутизации, доменов или TLS.

## Кандидаты на "ненужные"

В контексте именно `TrafficHub`:

- `searxng-local`
- `amnezia-xray`
- `mfo_api`

Но удалять их можно только если подтверждено, что ими не пользуются другие проекты на этом сервере.
