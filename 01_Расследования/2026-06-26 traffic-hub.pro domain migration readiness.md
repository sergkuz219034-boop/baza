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

## Выполнено 2026-06-26

### Симптом

DNS A-записи для нового домена были добавлены, но live runtime всё ещё держал старый домен `traffic-hubcrm.ru` как основной.

### Зона системы

- `/root/TrafficHub/.env`
- `/root/TrafficHub/deploy/Caddyfile`
- `/root/TrafficHub/docker-compose.yml`
- `/root/TrafficHub/dashboard/app.js`
- `/root/TrafficHub/modules/zarplata_api.py`
- `/root/TrafficHub/traffic_hub/config/settings.py`

### Гипотеза

Если просто переключить новый домен без alias, можно потерять доступ по старому `traffic-hubcrm.ru`. Нужен dual-domain режим: `.pro` как primary, `.ru` как fallback.

### Проверка

DNS:

- `traffic-hub.pro -> 150.241.70.31`
- `www.traffic-hub.pro -> 150.241.70.31`
- `am.traffic-hub.pro -> 150.241.70.31`
- `auth.traffic-hub.pro -> 150.241.70.31`

Runtime:

- `.env` переведён на `traffic-hub.pro`;
- `.env` сохраняет alias:
  - `PUBLIC_DOMAIN_ALT=traffic-hubcrm.ru`
  - `LICENSE_AUTH_DOMAIN_ALT=auth.traffic-hubcrm.ru`
  - `ACCOUNT_MANAGER_DOMAIN_ALT=am.traffic-hubcrm.ru`
  - `ACCOUNT_MANAGER_CORS_ORIGINS=https://am.traffic-hub.pro,https://am.traffic-hubcrm.ru`
- Caddy принимает оба auth-домена;
- Account Manager UI выбирает `am.traffic-hub.pro` для нового домена и `am.traffic-hubcrm.ru` для старого;
- default callback Зарплата.ру переведён на `https://traffic-hub.pro/auth/callback`.

### Наблюдение

После пересборки и recreate контейнеров:

- `traffichub_app` healthy;
- `traffichub_worker` healthy;
- `traffichub_license_auth` healthy;
- `traffichub_license_server` healthy;
- `traffichub_account_manager` healthy;
- `traffichub_caddy` running.

Внешние проверки без `-k`:

- `https://traffic-hub.pro/api/health` -> `200`, `status=ok`;
- `https://traffic-hub.pro/` -> HTML TrafficHub;
- `https://www.traffic-hub.pro/` -> HTML TrafficHub;
- `https://auth.traffic-hub.pro/health` -> `{"status":"ok"}`;
- `https://traffic-hubcrm.ru/api/health` -> `200`, `status=ok`;
- `https://auth.traffic-hubcrm.ru/health` -> `{"status":"ok"}`;
- `https://am.traffic-hub.pro/` и `https://am.traffic-hubcrm.ru/` -> `401 Unauthorized`, ожидаемо из-за Basic/Auth boundary.

### Вывод

Перенос выполнен без потери старого домена:

- primary domain: `traffic-hub.pro`;
- old public fallback: `traffic-hubcrm.ru`;
- Account Manager primary: `am.traffic-hub.pro`;
- Account Manager fallback: `am.traffic-hubcrm.ru`;
- Auth primary: `auth.traffic-hub.pro`;
- Auth fallback: `auth.traffic-hubcrm.ru`.

### Следующий шаг

Внешние интеграции, где callback URL задаётся вручную в кабинетах партнёров, нужно постепенно перевести на `https://traffic-hub.pro/auth/callback`. Старый callback `https://traffic-hubcrm.ru/auth/callback` остаётся рабочим на период совместимости.

### Фикс

Product commit: `0597d59f2` `feat: make traffic-hub.pro primary domain`.

Проверка:

- `python -m pytest -q tests/test_traffic_auth_external.py tests/test_account_manager_access.py tests/test_proxy_config.py tests/test_vbiv_bot_navigation.py tests/test_vbiv_bot_runtime_errors.py` -> `16 passed`;
- `docker compose config` -> ok;
- `docker compose --profile public config` -> ok;
- `caddy validate --config /etc/caddy/Caddyfile` -> valid;
- `/api/health` -> `status=ok`;
- GitHub checks на `0597d59f2`: `validate`, `windows-launcher`, `build-and-push` -> `success`.
