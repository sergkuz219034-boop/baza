# Env Separation Validation Checklist

Дата: 2026-06-01
Основано на:

- `05 Решения/2026-06-01 env separation change plan.md`
- `05 Решения/2026-06-01 env ownership map.md`
- `05 Решения/2026-06-01 operational map current deployment.md`

## Анализ

После каждой волны env separation нужно проверять не только “контейнеры поднялись”, но и пользовательские и интеграционные инварианты.

Иначе высок риск:

- принять частичную деградацию за успешную миграцию;
- не заметить auth drift;
- пропустить скрытую зависимость от legacy `.env`.

## Причина

### 1. Healthcheck не покрывает весь функционал

- Описание проблемы: `healthy` контейнер не гарантирует, что auth, integrations или perimeter работают корректно.
- Первопричина: deployment checks смотрят в основном на доступность процесса, а не на полную функциональную корректность.
- Критичность: `High`
- Возможные последствия:
  - ложноположительный вывод “миграция прошла успешно”;
  - позднее обнаружение regressions.
- Рекомендуемое исправление:
  - после каждой волны проверять отдельные функциональные инварианты по сервисам.

## План исправления

Использовать этот чек-лист сразу после каждой волны изменения env surface.

## Diff

### Волна 1. Shared + low-risk config

Что проверять:

1. Контейнеры:
- `autolead_server_bot` healthy
- `traffichub_license_auth` healthy
- `traffichub_account_manager` healthy
- `traffichub_caddy` up

2. Домены / маршрутизация:
- основной домен открывает dashboard
- `auth`-домен отвечает
- `am`-домен отвечает

3. UI / app:
- dashboard загружается
- статические ресурсы (`.js/.css`) не отдают 404
- `AccountManager` UI открывается

4. Конфигурационные флаги:
- legacy Sheets flags читаются как ожидалось
- `ACCOUNT_MANAGER_CORS_ORIGINS` не ломает фронт

Индикаторы регрессии:

- контейнер healthy, но UI не открывается;
- `caddy` проксирует не тот домен;
- фронт грузится без API.

### Волна 2. Partner / Telegram / AI secrets

Что проверять:

1. Partner integrations:
- partner API-запросы не падают на auth errors;
- связанные бизнес-сценарии выполняются;
- нет всплеска ошибок в логах `autolead_bot`.

2. Telegram:
- сценарии, завязанные на Telegram credentials, не падают;
- нет auth/permission ошибок по Telegram API.

3. AI / provider:
- AI/tooling requests не возвращают `401/403`;
- provider-specific integrations не деградировали.

Индикаторы регрессии:

- auth errors к внешним API;
- резкий рост retries;
- сценарии молча перестают работать без падения контейнера.

### Волна 3. Auth separation без rotation

Что проверять:

1. Login flow:
- пользовательский логин работает;
- redirect на login URL не сломан;
- logout/login cycle воспроизводим.

2. Token issuance / verification:
- `license_auth` продолжает выпускать/обслуживать связанный flow;
- downstream verify в `autolead_bot` не ломается;
- issuer/audience matching остаётся корректным.

3. AccountManager:
- middleware продолжает валидировать доступ;
- UI и API доступны в ожидаемом режиме;
- CORS не деградировал.

4. Shared secret question:
- если `SESSION_SECRET_KEY` оставлен общим, это осознанно задокументировано;
- если попытались разделить — отдельно проверено, что auth interoperability не сломалась.

Индикаторы регрессии:

- неожиданные `401/403`;
- циклические редиректы на login;
- “Auth is not configured” или похожие runtime-ошибки.

### Волна 4. Legacy `.env` cleanup

Что проверять:

1. Hidden dependency audit:
- ни один сервис не зависит от старого `.env`;
- все переменные реально читаются из новых env files.

2. Perimeter:
- `ACCOUNT_MANAGER_BASIC_AUTH_*` либо реально используются, либо окончательно удалены;
- `AI_AGENT_BASIC_AUTH_*` продолжают работать как ожидалось.

3. Final service sanity:
- все контейнеры healthy;
- домены отвечают;
- login и основные сценарии живы;
- integrations и AI/tooling не деградировали.

Индикаторы регрессии:

- после удаления legacy `.env` внезапно всплывает пропущенная переменная;
- сервис поднимается, но часть runtime-настроек silently missing.

## Риски

- Самый большой риск: ограничиться только `docker ps` и healthcheck'ами.
- Второй риск: не проверить auth flow отдельно от общей доступности UI.
- Третий риск: не посмотреть логи после волны и пропустить скрытые ошибки внешних интеграций.

## Проверка после исправления

Чек-лист считается полезным, если после каждой волны:

1. Есть явный набор pass/fail критериев.
2. Понятно, какой сервис и какой boundary сломался при регрессии.
3. Можно отделить config issue от integration/auth issue.

## Дополнительные улучшения

- Следующий уровень зрелости — автоматизировать часть этих проверок как smoke suite:
  - HTTP health + login route
  - domain reachability
  - basic auth checks
  - provider auth smoke checks
