# 2026-07-02 Двухконтурная схема контейнеров TrafficHub

## Симптом

После cleanup/оптимизации контейнеров возник риск считать `license_auth` и `license_server` мусором, потому что live product используется как SaaS.

## Зона системы

- Docker Compose: `/root/TrafficHub/docker-compose.yml`
- Reverse proxy: `/root/TrafficHub/deploy/Caddyfile`
- Auth/license: `license_auth`, `license_server`
- Local/download: `TrafficHub.exe`, `update.exe`, activation/license flow

## Гипотеза

`license_auth` и `license_server` могут быть legacy только для старого desktop-flow.

## Проверка

Проверено на live 2026-07-02:

- `docker compose ps` показывает healthy `traffichub_license_auth` и `traffichub_license_server`;
- `curl http://127.0.0.1:8400/health` возвращает `{"status":"ok"}`;
- `curl http://127.0.0.1:8401/health` возвращает `{"status":"ok"}`;
- `traffic-hub.pro`, `am.traffic-hub.pro`, `auth.traffic-hub.pro` остаются public routes;
- `license_server` не имеет публичного UI-route, но является внутренним license API кандидатом для local/download.

## Наблюдение

TrafficHub фактически двухконтурный:

- `Cloud/SaaS`: Docker/Caddy/PostgreSQL/Redis/app/worker/AccountManager/content bot/license_auth.
- `Local/download`: локальный запуск, `TrafficHub.exe`, `update.exe`, localhost callback, activation/license.

## Вывод

`license_auth` и `license_server` не удалять и не переименовывать без отдельного ADR. Оптимизация допустима на уровне build/image/healthcheck, но не через удаление local/download возможностей.

## Следующий шаг

Отдельно провести auth/license/download audit: endpoints, `TrafficHub.exe`, `update.exe`, `/api/system/update`, `utils.license`, activation/register flow и совместимость local callback.

