# Redacted Secret Inventory

Дата: 2026-06-01
Источник фактов:

- live `.env` read in redacted form
- `docker-compose.yml`
- `deploy/Caddyfile`

Значения секретов в документ **не включаются**.

## Анализ

Live `.env` подтверждает, что в одном файле одновременно лежат:

- app/session secrets
- external auth settings
- perimeter/basic auth hashes
- partner credentials
- LLM/provider API keys
- Telegram credentials

По compose подтверждено, что этот `.env` влияет сразу на несколько сервисов:

- `autolead_bot`
- `license_auth`
- `account_manager`
- `caddy`

## Причина

### 1. Secret sprawl в одном env surface

- Описание проблемы: один `.env` является общей точкой конфигурации для нескольких сервисов и нескольких классов секретов.
- Первопричина: deployment использует единый env-file как универсальное хранилище.
- Критичность: `Critical`
- Возможные последствия:
  - единичная утечка файла компрометирует сразу несколько контуров;
  - ротация становится широкой и рискованной;
  - сложно отделить blast radius по сервисам.
- Рекомендуемое исправление:
  - разнести секреты по сервисам;
  - уменьшить общий env surface;
  - отделить конфигурацию от credential material.

## План исправления

1. Сначала провести инвентаризацию по классам и сервисам.
2. Затем выделить самые критичные классы для приоритетной ротации.
3. После этого разнести секреты по отдельным env surfaces / secure stores.

## Diff

### 1. Секреты / параметры уровня всего deployment

- `SESSION_SECRET_KEY`
- `PUBLIC_DOMAIN`
- `LICENSE_AUTH_DOMAIN`
- `PUBLIC_BASE_URL`
- `AUTH_MODE`

### 2. External auth / license auth

- `EXTERNAL_AUTH_ALGORITHM`
- `EXTERNAL_AUTH_VERIFY_KEY_PATH`
- `EXTERNAL_AUTH_ISSUER`
- `EXTERNAL_AUTH_AUDIENCE`
- `EXTERNAL_AUTH_LOGIN_URL`
- `LICENSE_AUTH_ISSUER`
- `LICENSE_AUTH_AUDIENCE`
- `LICENSE_AUTH_ALGORITHM`
- `LICENSE_AUTH_PRIVATE_KEY_PATH`
- `LICENSE_AUTH_LOGIN_TITLE`

Сервисы:

- `autolead_bot`
- `license_auth`

Blast radius:

- вход пользователей;
- external token verification;
- issuer/signing path.

### 3. AccountManager perimeter / auth

- `ACCOUNT_MANAGER_DOMAIN`
- `ACCOUNT_MANAGER_CORS_ORIGINS`
- `ACCOUNT_MANAGER_BASIC_AUTH_USER`
- `ACCOUNT_MANAGER_BASIC_AUTH_HASH`
- `ACCOUNT_MANAGER_PORT`

Сервисы:

- `account_manager`
- `caddy`

Blast radius:

- внешний доступ к AccountManager;
- CORS/perimeter assumptions;
- reverse proxy auth drift.

### 4. AI perimeter

- `AI_AGENT_BASIC_AUTH_USER`
- `AI_AGENT_BASIC_AUTH_HASH`

Сервис:

- `caddy`

Blast radius:

- защита AI perimeter.

### 5. Partner / business credentials

- `LEADSU_API_TOKEN`
- `LEADSU_EMAIL`
- `LEADSU_PASSWORD`
- `LOVKO_EMAIL`
- `LOVKO_PASSWORD`
- `MFO_DOMAIN`

Сервисы:

- в первую очередь `autolead_bot`

Blast radius:

- внешние партнерские кабинеты и API;
- нарушение бизнес-процессов сбора/обработки лидов.

### 6. Telegram credentials

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_BOT_TOKEN`

Сервисы:

- связанный automation / integration layer

Blast radius:

- доступ к Telegram integrations и связанным сценариям.

### 7. LLM / external AI providers

- `DEEPSEEK_API_KEY`
- `FREELMAPI_API_KEY`
- `OPENROUTER_API_KEY`
- `CLOSEROUTER_API_KEY`

Сервисы:

- AI / tooling layer

Blast radius:

- внешние provider quotas;
- несанкционированное использование paid APIs;
- leakage of automation workflows.

### 8. Non-secret, но влияющие на runtime flags

- `CONTROL_LEGACY_SHEETS_FALLBACK`
- `CONTROL_LEGACY_SHEETS_DUAL_WRITE`

Сервисы:

- `autolead_bot`

Blast radius:

- migration behavior / legacy sync mode;
- функциональные расхождения, а не прямой security leak.

## Риски

- Самый большой риск: один `.env` даёт доступ сразу к auth, business integrations, AI providers и perimeter configs.
- Второй риск: часть переменных воспринимается как “обычный конфиг”, хотя по факту это credentials.
- Третий риск: reverse proxy drift для `AccountManager` маскирует реальный security posture.

## Проверка после исправления

Инвентаризация уже подтверждена через:

- redacted вывод live `.env`
- сопоставление с `docker-compose.yml`
- сопоставление с `Caddyfile`

## Дополнительные улучшения

- Следующий шаг: сделать приоритизированный rotation plan по классам:
  - `Critical`
  - `High`
  - `Medium`
- Затем уже можно планировать разнесение env surface по сервисам без хаотической миграции.
