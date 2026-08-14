# 2026-06-30 Caddy backend outage maintenance fallback

## Симптом

- Во время `docker compose up --build autolead_bot worker` пользователи могли видеть raw browser error или 502.
- В Caddy logs повторялось: `lookup autolead_bot on 127.0.0.11:53: no such host`.

## Зона системы

- `deploy/Caddyfile`
- Docker Compose service `autolead_bot`
- Caddy reverse proxy на `traffic-hub.pro`

## Гипотеза

- При пересоздании контейнера Docker на короткое время удаляет DNS alias `autolead_bot`.
- Caddy в этот момент не может резолвить upstream и отдаёт 502, хотя это нормальное deploy-window состояние.

## Проверка

- Live `docker compose ps` показал service `autolead_bot` с container name `traffichub_app`.
- `deploy/Caddyfile` проксировал public domain на `autolead_bot:8080`.
- Caddy logs за последние 6 часов содержали несколько `lookup autolead_bot ... no such host` на `/api/logs`, `/api/jobs/status`, `/ws/log`, `/ws/status`.
- App health при этом после deploy был OK.

## Наблюдение

- Это не business/runtime bug Autolead.
- Это инфраструктурный deploy-gap: backend контейнер здоров после старта, но во время recreate upstream alias временно отсутствует.

## Вывод

- Нельзя полагаться только на включение техработ в app, если сам app недоступен.
- Reverse proxy должен иметь fallback на уровне Caddy.

## Исправление

- Product commit: `746e7f483 fix: show maintenance page on backend outage`.
- В `deploy/Caddyfile` добавлен snippet `backend_unavailable_notice`.
- Для public domain `traffic-hub.pro` и legacy domain `traffic-hubcrm.ru` добавлен `handle_errors`, который отдаёт HTML-экран `Тех работы` при backend outage.

## Подтверждение

- `caddy validate --config /etc/caddy/Caddyfile`: valid.
- GitHub checks for commit `746e7f483`: `CI` success, `Build and Push Docker Image` success.
- `docker compose up -d caddy` применил конфиг.
- `https://traffic-hub.pro/api/health` вернул `status=ok`.
- После reload свежих Caddy `502/no such host/connect refused` в проверочном окне не найдено.

## Следующий шаг

- При будущих deploy больше не считать краткий backend restart пользовательским `ERR_CONNECTION_CLOSED`: пользователь должен видеть controlled maintenance page.
- Если 502 появляется не во время deploy, проверять уже `docker compose ps`, healthcheck app и Caddy upstream network.

