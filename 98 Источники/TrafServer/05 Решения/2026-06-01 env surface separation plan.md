# Env Surface Separation Plan

Дата: 2026-06-01
Основано на:

- `05 Решения/2026-06-01 redacted secret inventory.md`
- `05 Решения/2026-06-01 operational map current deployment.md`
- `docker-compose.yml`
- live redacted `.env`

## Анализ

Текущее состояние:

- один `.env` обслуживает сразу `autolead_bot`, `license_auth`, `account_manager`, `caddy`;
- внутри одного файла смешаны:
  - app config,
  - auth settings,
  - signing/verification settings,
  - perimeter credentials,
  - partner credentials,
  - AI/provider keys.

Это означает, что конфигурационный surface сейчас слишком широкий и плохо делится по ownership.

По compose видно:

- `autolead_bot` читает и собственные runtime-переменные, и auth-related настройки;
- `license_auth` читает только свой поднабор auth/signing-конфига;
- `account_manager` использует свой поднабор app/auth-конфига;
- `caddy` использует только домены и basic auth hashes.

Следовательно, разделение возможно без глубокой смены архитектуры.

## Причина

### 1. Слишком широкий общий `.env`

- Описание проблемы: один env-file является общей точкой для нескольких сервисов.
- Первопричина: deployment эволюционировал вокруг одного `.env`, в который постепенно добавлялись новые подсистемы.
- Критичность: `High`
- Возможные последствия:
  - высокий blast radius;
  - трудно проводить ротацию и дебаг;
  - одна ошибка в env management затрагивает сразу несколько сервисов.
- Рекомендуемое исправление:
  - разделить env surface по сервисам и типам секретов.

## План исправления

### Целевой принцип

Не менять прикладную архитектуру шире необходимости. Достаточно перейти от одного общего `.env` к нескольким service-scoped env files.

### Минимальная целевая схема

1. Общий non-secret конфиг:

- `.env.shared`

Содержит только:

- домены;
- публичные URL;
- не чувствительные runtime flags;
- возможно общие timezone/ports, если это действительно shared config.

2. Autolead runtime:

- `.env.autolead`

Содержит:

- `SESSION_SECRET_KEY` только если он реально нужен именно этому сервису;
- `AUTH_MODE`
- `EXTERNAL_AUTH_*`
- partner credentials (`LEADSU_*`, `LOVKO_*`, etc.)
- AI/provider keys, если они используются именно этим сервисом
- Telegram credentials, если они используются именно этим сервисом

3. License Auth:

- `.env.license_auth`

Содержит:

- `LICENSE_AUTH_*`
- signing / issuer / audience material
- только те ключи, которые нужны сервису issuer/verifier

4. AccountManager:

- `.env.account_manager`

Содержит:

- `SESSION_SECRET_KEY`, если этот сервис использует тот же секрет осознанно;
- `ACCOUNT_MANAGER_*`
- только его app-specific runtime config

5. Caddy:

- `.env.caddy`

Содержит:

- `PUBLIC_DOMAIN`
- `LICENSE_AUTH_DOMAIN`
- `ACCOUNT_MANAGER_DOMAIN`
- `AI_AGENT_DOMAIN`
- `ACCOUNT_MANAGER_BASIC_AUTH_*`
- `AI_AGENT_BASIC_AUTH_*`

### Что можно оставить общим

Только низкорисковые значения:

- доменные имена;
- не чувствительные feature flags;
- возможно локальные bind ports.

### Что нельзя оставлять в общем `.env`

По возможности вынести:

- signing / verification secrets;
- provider API keys;
- partner credentials;
- Telegram secrets;
- basic auth hashes;
- session secrets, если их не обязаны делить несколько сервисов.

## Diff

### Текущая схема

```diff
- .env
```

### Целевая схема

```diff
+ .env.shared
+ .env.autolead
+ .env.license_auth
+ .env.account_manager
+ .env.caddy
```

### Минимальное изменение в compose

Идея:

```diff
services:
  autolead_bot:
    env_file:
-      - path: .env
+      - path: .env.shared
+      - path: .env.autolead

  license_auth:
    env_file:
-      - path: .env
+      - path: .env.shared
+      - path: .env.license_auth

  account_manager:
    env_file:
-      - path: .env
+      - path: .env.shared
+      - path: .env.account_manager

  caddy:
    env_file:
+      - path: .env.shared
+      - path: .env.caddy
```

Почему это изменение выглядит безопасным:

- env_file уже используется в compose;
- схема не требует переписывать код приложений;
- мы меняем только источник переменных, а не приложение.

### Побочные эффекты

- если одна и та же переменная сейчас неявно используется несколькими сервисами, это вскроется;
- потребуется аккуратно зафиксировать ownership каждой переменной;
- возможны регрессии при первой неполной раскладке env files.

## Риски

- Самый большой риск: вынести переменную не в тот service-scoped env и получить hidden runtime failure.
- Второй риск: случайно разделить секрет, который намеренно общий между несколькими сервисами.
- Третий риск: одновременно совмещать separation и rotation; лучше делать это в разные окна изменений.

## Проверка после исправления

После разнесения env surface нужно проверить по сервисам:

### Autolead

- контейнер стартует;
- dashboard и jobs работают;
- partner integrations и related auth не деградировали.

### License Auth

- issuer работает;
- токены продолжают валидироваться downstream сервисами.

### AccountManager

- логин и middleware работают;
- CORS и app runtime не деградировали.

### Caddy

- все домены резолвятся на нужные backend routes;
- perimeter auth ведёт себя ожидаемо.

## Дополнительные улучшения

- После separation уже безопаснее делать rotation wave-by-wave.
- Следующий зрелый шаг — увести самые критичные secret classes из env files вообще, в отдельное защищённое хранилище или managed secret layer.
