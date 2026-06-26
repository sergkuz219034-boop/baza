# 2026-06-26 traffic-hub.pro domain migration readiness

## Симптом

Нужно проверить, можно ли переносить TrafficHub на домен `traffic-hub.pro`.

## Зона системы

- DNS: `traffic-hub.pro`, `www.traffic-hub.pro`, `am.traffic-hub.pro`, `auth.traffic-hub.pro`.
- Reverse proxy: `/root/TrafficHub/deploy/Caddyfile`.
- Runtime env: `/root/TrafficHub/.env`, `docker-compose.yml`.
- Frontend абсолютные ссылки: `/root/TrafficHub/dashboard/app.js`.

## Гипотеза

Основной домен уже может быть направлен на live-сервер, но полный перенос может быть неполным из-за старых абсолютных URL `traffic-hubcrm.ru`.

## Проверка

- `Resolve-DnsName traffic-hub.pro -Type A`
- `Resolve-DnsName www.traffic-hub.pro -Type A`
- `Resolve-DnsName am.traffic-hub.pro -Type A`
- `Resolve-DnsName auth.traffic-hub.pro -Type A`
- `curl -I https://traffic-hub.pro/`
- `curl -I https://www.traffic-hub.pro/`
- `curl -I http://traffic-hub.pro/`
- `curl -I https://am.traffic-hub.pro/`
- `docker exec traffichub_caddy caddy validate --config /etc/caddy/Caddyfile`
- `rg 'traffic-hubcrm\.ru|am\.traffic|auth\.traffic|PUBLIC_BASE|callback' /root/TrafficHub`

## Наблюдение

- `traffic-hub.pro` указывает на `150.241.70.31`.
- `www.traffic-hub.pro` указывает на `150.241.70.31`.
- `am.traffic-hub.pro` указывает на `150.241.70.31`.
- `auth.traffic-hub.pro` не резолвится.
- `https://traffic-hub.pro/` возвращает `200 OK`.
- `https://www.traffic-hub.pro/` возвращает `200 OK`.
- `http://traffic-hub.pro/` возвращает `308 Permanent Redirect` на HTTPS.
- `https://am.traffic-hub.pro/` доходит до Caddy и возвращает `401 Unauthorized`, то есть домен маршрутизируется к Account Manager.
- Caddy config валиден.
- `/root/TrafficHub/deploy/Caddyfile` уже содержит site labels:
  - `{$PUBLIC_DOMAIN:traffic-hubcrm.ru}`
  - `{$PUBLIC_DOMAIN_ALT:traffic-hub.pro}`
  - `{$PUBLIC_WWW_DOMAIN_ALT:www.traffic-hub.pro}`
  - `{$ACCOUNT_MANAGER_DOMAIN:am.traffic-hubcrm.ru}`
  - `{$ACCOUNT_MANAGER_DOMAIN_ALT:am.traffic-hub.pro}`
- `/root/TrafficHub/.env` всё ещё использует старый основной домен:
  - `PUBLIC_DOMAIN=traffic-hubcrm.ru`
  - `PUBLIC_BASE_URL=https://traffic-hubcrm.ru`
  - `LICENSE_AUTH_DOMAIN=auth.traffic-hubcrm.ru`
  - `EXTERNAL_AUTH_ISSUER=https://auth.traffic-hubcrm.ru`
  - `EXTERNAL_AUTH_LOGIN_URL=https://auth.traffic-hubcrm.ru/login`
  - `ACCOUNT_MANAGER_DOMAIN=am.traffic-hubcrm.ru`
  - `ACCOUNT_MANAGER_CORS_ORIGINS=https://am.traffic-hubcrm.ru`
- `/root/TrafficHub/dashboard/app.js` содержит hardcoded old-domain места:
  - `am.traffic-hubcrm.ru`
  - `https://am.traffic-hubcrm.ru/`
  - `https://traffic-hubcrm.ru/auth/callback`
- `modules/zarplata_api.py` содержит default callback `https://traffic-hubcrm.ru/auth/callback`.

## Вывод

`traffic-hub.pro` уже готов как дополнительный публичный домен для основного TrafficHub UI: DNS, HTTPS и Caddy-маршрутизация работают.

Полный перенос primary-домена пока не завершён. Причина: часть runtime env, auth issuer/login URL, Account Manager URL, CORS и callback defaults всё ещё указывают на `traffic-hubcrm.ru`.

## Следующий шаг

Безопасный порядок полного переноса:

1. Добавить DNS `A auth -> 150.241.70.31`, если license/auth должен жить на новом домене.
2. Добавить Caddy site label для `auth.traffic-hub.pro`.
3. Перевести env на новый домен:
   - `PUBLIC_DOMAIN=traffic-hub.pro`
   - `PUBLIC_BASE_URL=https://traffic-hub.pro`
   - `LICENSE_AUTH_DOMAIN=auth.traffic-hub.pro`
   - `EXTERNAL_AUTH_ISSUER=https://auth.traffic-hub.pro`
   - `EXTERNAL_AUTH_LOGIN_URL=https://auth.traffic-hub.pro/login`
   - `LICENSE_AUTH_ISSUER=https://auth.traffic-hub.pro`
   - `ACCOUNT_MANAGER_DOMAIN=am.traffic-hub.pro`
   - `ACCOUNT_MANAGER_CORS_ORIGINS=https://am.traffic-hub.pro`
4. Заменить hardcoded frontend URLs на origin/domain-aware config.
5. Обновить callback URLs в Rabota.ru/Zarplata.ru/Google integrations.
6. Пересобрать и пересоздать контейнеры.
7. Проверить:
   - `https://traffic-hub.pro/api/health`
   - login/logout
   - admin panel
   - Account Manager open flow
   - OAuth callback
   - WebSocket logs/status

