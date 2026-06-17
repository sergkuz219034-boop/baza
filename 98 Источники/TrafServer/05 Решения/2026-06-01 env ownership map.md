# Env Ownership Map

Дата: 2026-06-01
Основано на:

- `docker-compose.yml`
- live redacted `.env`
- `05 Решения/2026-06-01 redacted secret inventory.md`
- `05 Решения/2026-06-01 secret rotation priority plan.md`
- `05 Решения/2026-06-01 env surface separation plan.md`

Значения переменных в документ **не включаются**.

## Анализ

Цель этой карты — для каждой важной env-переменной определить:

- кто её читает;
- это secret или обычный config;
- должна ли она быть `shared` или `service-scoped`;
- в какую волну ротации она попадает;
- какой риск несёт неправильное размещение.

Это не список “всех возможных env”, а ownership-карта для переменных, которые уже подтверждены в live deployment как значимые.

## Причина

### 1. Без ownership map separation и rotation будут слишком хрупкими

- Описание проблемы: без явного владельца переменной легко вынести её не в тот env file.
- Первопричина: текущий `.env` исторически был общим для всех сервисов.
- Критичность: `High`
- Возможные последствия:
  - скрытые runtime-фейлы;
  - auth drift;
  - сложность локализации регрессии.
- Рекомендуемое исправление:
  - ввести ownership map до реального разнесения env surface.

## План исправления

1. Использовать эту карту как спецификацию для env separation.
2. Сначала переносить `service-scoped` переменные.
3. `shared` оставлять только там, где это действительно оправдано.
4. Rotation выполнять после separation или отдельными волнами.

## Diff

### 1. Shared non-secret / low-secret config

Эти переменные могут оставаться в `.env.shared`, если они действительно общие:

| Переменная | Сервис(ы) | Тип | Целевой scope | Ротация | Комментарий |
|---|---|---|---|---|---|
| `PUBLIC_DOMAIN` | `caddy`, косвенно UI/docs | config | `shared` | `Low` | Домен основного контура |
| `LICENSE_AUTH_DOMAIN` | `caddy`, auth links | config | `shared` | `Low` | Домен auth-контура |
| `ACCOUNT_MANAGER_DOMAIN` | `caddy`, app links | config | `shared` | `Low` | Но perimeter auth для него сейчас drift |
| `PUBLIC_BASE_URL` | `autolead_bot` | config | `shared` или `autolead` | `Low` | Можно оставить shared, если действительно один public URL |
| `ACCOUNT_MANAGER_PORT` | `account_manager` | config | `account_manager` | `Low` | Формально не shared |

### 2. Auth / session / perimeter secrets

Это критичные переменные. Их нельзя держать в общем env surface без сильной причины.

| Переменная | Сервис(ы) | Тип | Целевой scope | Ротация | Комментарий |
|---|---|---|---|---|---|
| `SESSION_SECRET_KEY` | `autolead_bot`, `account_manager` | secret | требует явного решения | `Critical` | Сейчас shared secret между 2 контурами; нужно решить, это осознанно или legacy coupling |
| `EXTERNAL_AUTH_ALGORITHM` | `autolead_bot` | config/auth | `autolead` | `Critical` | Должно жить рядом с downstream verifier config |
| `EXTERNAL_AUTH_VERIFY_KEY_PATH` | `autolead_bot` | secret path | `autolead` | `Critical` | Привязано к verify layer |
| `EXTERNAL_AUTH_ISSUER` | `autolead_bot` | auth config | `autolead` | `Critical` | Auth boundary |
| `EXTERNAL_AUTH_AUDIENCE` | `autolead_bot` | auth config | `autolead` | `Critical` | Auth boundary |
| `EXTERNAL_AUTH_LOGIN_URL` | `autolead_bot` | auth config | `autolead` | `Critical` | Login redirect boundary |
| `LICENSE_AUTH_ISSUER` | `license_auth` | auth config | `license_auth` | `Critical` | Issuer side |
| `LICENSE_AUTH_AUDIENCE` | `license_auth` | auth config | `license_auth` | `Critical` | Issuer side |
| `LICENSE_AUTH_ALGORITHM` | `license_auth` | auth config | `license_auth` | `Critical` | Issuer side |
| `LICENSE_AUTH_PRIVATE_KEY_PATH` | `license_auth` | secret path | `license_auth` | `Critical` | Signing material |
| `ACCOUNT_MANAGER_BASIC_AUTH_USER` | `caddy` | perimeter config | `caddy` | `Low/Medium` | Сейчас env есть, but no effective use |
| `ACCOUNT_MANAGER_BASIC_AUTH_HASH` | `caddy` | secret/perimeter | `caddy` | `Critical` if used | Сейчас drift: stored but not applied |
| `AI_AGENT_BASIC_AUTH_USER` | `caddy` | perimeter config | `caddy` | `Medium` | Used by AI perimeter |
| `AI_AGENT_BASIC_AUTH_HASH` | `caddy` | secret/perimeter | `caddy` | `Critical` | External-facing gate |

### 3. Business / partner credentials

Их логично вынести в `.env.autolead` или отдельный integrations env.

| Переменная | Сервис(ы) | Тип | Целевой scope | Ротация | Комментарий |
|---|---|---|---|---|---|
| `LEADSU_API_TOKEN` | `autolead_bot` | secret | `autolead` | `High` | Partner API |
| `LEADSU_EMAIL` | `autolead_bot` | credential | `autolead` | `High` | Partner account |
| `LEADSU_PASSWORD` | `autolead_bot` | credential | `autolead` | `High` | Partner account |
| `LOVKO_EMAIL` | `autolead_bot` | credential | `autolead` | `High` | Partner account |
| `LOVKO_PASSWORD` | `autolead_bot` | credential | `autolead` | `High` | Partner account |
| `MFO_DOMAIN` | integration layer | config | `autolead` or integration-specific | `Medium` | Not secret by itself, but belongs with integration config |

### 4. Telegram

| Переменная | Сервис(ы) | Тип | Целевой scope | Ротация | Комментарий |
|---|---|---|---|---|---|
| `TELEGRAM_API_ID` | integration layer | secret | `autolead` or integrations env | `High` | Communication boundary |
| `TELEGRAM_API_HASH` | integration layer | secret | `autolead` or integrations env | `High` | Communication boundary |
| `TELEGRAM_BOT_TOKEN` | integration layer | secret | `autolead` or integrations env | `High` | Bot takeover risk |

### 5. AI / provider keys

| Переменная | Сервис(ы) | Тип | Целевой scope | Ротация | Комментарий |
|---|---|---|---|---|---|
| `DEEPSEEK_API_KEY` | AI/tooling | secret | `autolead` or AI env | `Medium` | Provider key |
| `FREELMAPI_API_KEY` | AI/tooling | secret | `autolead` or AI env | `Medium` | Provider key |
| `OPENROUTER_API_KEY` | AI/tooling | secret | `autolead` or AI env | `Medium` | Provider key |
| `CLOSEROUTER_API_KEY` | AI/tooling | secret | `autolead` or AI env | `Medium` | Provider key |

### 6. Runtime / migration flags

| Переменная | Сервис(ы) | Тип | Целевой scope | Ротация | Комментарий |
|---|---|---|---|---|---|
| `AUTH_MODE` | `autolead_bot` | config | `autolead` | `Low` | Security-relevant mode flag |
| `CONTROL_LEGACY_SHEETS_FALLBACK` | `autolead_bot` | config | `autolead` | `Low` | Functional flag |
| `CONTROL_LEGACY_SHEETS_DUAL_WRITE` | `autolead_bot` | config | `autolead` | `Low` | Functional flag |
| `ACCOUNT_MANAGER_CORS_ORIGINS` | `account_manager` | config | `account_manager` | `Low` | App-specific |
| `LICENSE_AUTH_LOGIN_TITLE` | `license_auth` | config | `license_auth` | `Low` | Cosmetic/app-specific |

## Риски

### Shared-by-default risk

- `SESSION_SECRET_KEY` сейчас самый чувствительный случай: он выглядит как общий секрет между `autolead_bot` и `account_manager`.
- Если это случайное наследие, его разделение уменьшит blast radius.
- Если это осознанный контракт, его разделение сломает auth interoperability.

### Drift risk

- `ACCOUNT_MANAGER_BASIC_AUTH_*` — пример переменных, у которых есть owner (`caddy`), но нет фактического применения.
- Такие переменные особенно опасны как источник ложных assumptions.

### Hidden consumer risk

- Некоторые значения могут использоваться не только явным контейнером, но и scripts/tools around deployment.
- Перед separation нужно проверять не только compose, но и operational tooling.

## Проверка после исправления

Эта карта считается корректной, если после будущего separation:

1. Каждая переменная живёт в env file того сервиса, который реально её использует.
2. В `.env.shared` остаются только действительно shared config values.
3. Security-sensitive переменные не лежат “на всякий случай” в общей конфигурации.
4. `ACCOUNT_MANAGER_BASIC_AUTH_*` либо реально используются, либо удалены.

## Дополнительные улучшения

- Следующий шаг: сделать change plan по migration waves:
  - сначала перенести `service-scoped` config без ротации;
  - потом ротировать `Critical`;
  - затем `High`;
  - затем `Medium`.
- Это даст минимальный операционный риск и максимальную наблюдаемость регрессий.
