# Hermes remote gateway container

Теги: #сущность #hermes #docker #deployment

## Назначение

`traffichub_hermes` даёт официальный Hermes Agent dashboard/gateway для подключения Hermes Desktop в режиме `Remote gateway`.

Канонический URL:

```text
https://traffic-hubcrm.ru/hermes
```

## Почему так

Старый контур `hermes-workspace.service` запускал отдельный Vite Workspace на `:3000` и был привязан к AccountManager/Victoria recruiter bridge. Для Hermes Desktop нужен gateway, который отвечает на `/api/status` и умеет отдавать dashboard auth. Поэтому gateway вынесен в Docker Compose как отдельный сервис.

## Runtime-факты

- server repo: `/root/TrafficHub`
- compose service: `hermes`
- container: `traffichub_hermes`
- image: `traffichub-hermes-agent:local`
- build context: `/usr/local/lib/hermes-agent`
- internal dashboard port: `9119`
- persistent home: `/home/codex/.hermes -> /opt/data`
- public route: `https://traffic-hubcrm.ru/hermes`
- health endpoint: `https://traffic-hubcrm.ru/hermes/api/status`
- auth: `basic`
- old services: `hermes-workspace.service` and `victoria-recruiter-gateway.service` disabled after migration

## Caddy contract

Public domain route:

```text
/hermes* -> hermes:9119
```

Required proxy headers:

- `X-Forwarded-Prefix: /hermes`
- `X-Forwarded-Proto: https`

Без `X-Forwarded-Prefix` Hermes dashboard строит login URL как `/login`, что ломает публикацию под path-prefix.

## Compose contract

Ключевые env:

- `HERMES_DASHBOARD=1`
- `HERMES_DASHBOARD_HOST=0.0.0.0`
- `HERMES_DASHBOARD_PORT=9119`
- `HERMES_DASHBOARD_PUBLIC_URL=https://traffic-hubcrm.ru/hermes`
- `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`
- `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`
- `HERMES_DASHBOARD_BASIC_AUTH_SECRET`

Секреты должны жить в серверном `.env`, а не в tracked `docker-compose.yml`.

## Проверка

```bash
cd /root/TrafficHub
docker compose ps hermes caddy
curl -k https://traffic-hubcrm.ru/hermes/api/status
curl -k https://traffic-hubcrm.ru/hermes/login
systemctl is-active hermes-workspace.service victoria-recruiter-gateway.service
```

Ожидаемо:

- `traffichub_hermes` healthy
- `/hermes/api/status` возвращает `200`
- `/hermes/login` отдаёт страницу `Sign in — Hermes Agent`
- старые systemd-сервисы не активны

## Ограничения

- `hermes.traffic-hubcrm.ru` подготовлен в Caddy, но не является рабочим каноном без DNS-записи.
- Session token не инжектится в HTML, когда включён `auth_required=true`; Desktop должен использовать basic auth flow.
- Контейнер не публикует порт `9119` наружу, доступ только через Caddy.

## Связанные страницы

- [[2026-06-26 Hermes remote gateway container]]
- [[Hermes Workspace live publish]]
- [[Victoria recruiter gateway]]
- [[Deployment]]
