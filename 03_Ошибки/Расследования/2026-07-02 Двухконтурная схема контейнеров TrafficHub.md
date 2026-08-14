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

Дополнительный audit показал, что `license_auth` и `license_server` не являются дублями:

- `license_auth` — public login/JWT gateway (`/login`, `/token`);
- `license_server` — internal signed license-key API (`/keys/create`, `/keys/validate/{key}`, `/keys/revoke`);
- local/download build действительно собирает `TrafficHub.exe`, `update.exe`, `ActivateLicense.exe`, `AccountManager.exe` и optional `LicenseKeygen.exe`.

## Вывод

`license_auth` и `license_server` не удалять и не переименовывать без отдельного ADR. Оптимизация допустима на уровне build/image/healthcheck, но не через удаление local/download возможностей.

## Следующий шаг

Отдельно провести auth/license/download audit: endpoints, `TrafficHub.exe`, `update.exe`, `/api/system/update`, `utils.license`, activation/register flow и совместимость local callback.

Audit частично выполнен и зафиксирован в product docs `docs/auth-license-download-audit.md`. Открытым остаётся end-to-end тест Windows artifact flow и решение, остаётся ли `license_server` cloud-service, local/download-only service или объединяется с `license_auth`.
