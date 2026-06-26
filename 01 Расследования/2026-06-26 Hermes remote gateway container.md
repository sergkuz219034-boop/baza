# 2026-06-26 Hermes remote gateway container

Теги: #расследование #hermes #deployment

## Симптом

Hermes Desktop в режиме `Remote gateway` не мог подключиться к `https://traffic-hubcrm.ru/hermes`: приложение показывало `Remote gateway incomplete` и просило рабочий remote URL/session token.

## Зона системы

- сервер `150.241.70.31`
- `/root/TrafficHub/docker-compose.yml`
- `/root/TrafficHub/deploy/Caddyfile`
- контейнер `traffichub_hermes`
- старые systemd-сервисы `hermes-workspace.service` и `victoria-recruiter-gateway.service`

## Гипотеза

Для Hermes Desktop нужен не старый Vite Workspace на `:3000`, а официальный Hermes dashboard/gateway, опубликованный через Caddy и доступный по стабильному HTTPS URL.

## Проверка

- Проверена документация Hermes Agent в установленном пакете `/usr/local/lib/hermes-agent/website/docs/user-guide/docker.md`.
- Подтверждено, что dashboard должен запускаться в том же контейнере через `HERMES_DASHBOARD=1`.
- Проверен endpoint `GET https://traffic-hubcrm.ru/hermes/api/status`.
- Проверен route `GET https://traffic-hubcrm.ru/hermes/login`.
- Проверены контейнеры `docker compose ps hermes caddy`.
- Проверены старые systemd-сервисы.

## Наблюдение

- Контейнер `traffichub_hermes` поднят из локального образа `traffichub-hermes-agent:local`.
- Внутри контейнера dashboard слушает `0.0.0.0:9119`.
- Caddy публикует gateway под `https://traffic-hubcrm.ru/hermes`.
- Для path-prefix нужен header `X-Forwarded-Prefix: /hermes`; без него dashboard редиректил на корневой `/login`.
- `GET /hermes/api/status` публично отвечает `200` и показывает `auth_required=true`, `auth_providers=["basic"]`.
- Старые `hermes-workspace.service` и `victoria-recruiter-gateway.service` остановлены и отключены, чтобы не было двух разных Hermes-контуров.
- Изменения конфигурации закоммичены на сервере и отправлены на GitHub коммитом `8ac63eeef`.

## Вывод

Актуальный remote gateway для Hermes Desktop:

```text
https://traffic-hubcrm.ru/hermes
```

Это Docker-контур, а не legacy systemd/Vite Workspace.

## Следующий шаг

- В Hermes Desktop указать `Remote URL = https://traffic-hubcrm.ru/hermes`.
- Если desktop запросит авторизацию, использовать basic provider.
- Если потребуется отдельный поддомен `hermes.traffic-hubcrm.ru`, сначала добавить DNS `A`-запись на `150.241.70.31`; Caddy-блок под этот домен уже подготовлен, но без DNS он не будет резолвиться.

## Связанные страницы

- [[Hermes remote gateway container]]
- [[Hermes Workspace live publish]]
- [[Deployment]]
