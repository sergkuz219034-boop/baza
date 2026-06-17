# Env Separation Change Plan

Дата: 2026-06-01
Основано на:

- `05 Решения/2026-06-01 env ownership map.md`
- `05 Решения/2026-06-01 env surface separation plan.md`
- `05 Решения/2026-06-01 secret rotation priority plan.md`
- `05 Решения/2026-06-01 operational map current deployment.md`

## Анализ

Разносить `.env` по сервисам нужно не одной большой миграцией, а по волнам. Иначе:

- трудно понять, какой сервис сломался из-за какого переноса;
- легко смешать separation и rotation;
- можно получить каскадную деградацию auth/perimeter flows.

Текущее deployment-окружение позволяет делать это постепенно, потому что:

- сервисы уже разделены на отдельные контейнеры;
- compose уже использует `env_file`;
- сервисы имеют отдельные healthcheck'и.

## Причина

### 1. Нужен change plan, а не только концептуальная схема

- Описание проблемы: ownership map и separation plan отвечают на вопрос “куда что должно попасть”, но не на вопрос “в какой последовательности внедрять”.
- Первопричина: у env surface есть межсервисные зависимости, и они не одинаково рискованны.
- Критичность: `High`
- Возможные последствия:
  - неверный порядок внедрения даст ложные регрессии;
  - можно сломать сразу auth и integrations.
- Рекомендуемое исправление:
  - внедрять separation волнами, с отдельной проверкой после каждой.

## План исправления

### Волна 0. Подготовка без изменения runtime

Цель:

- подготовить новые env files без подключения их в compose.

Что сделать:

- создать:
  - `.env.shared`
  - `.env.autolead`
  - `.env.license_auth`
  - `.env.account_manager`
  - `.env.caddy`
- разложить переменные по ownership map;
- пока не трогать `docker-compose.yml`.

Почему это безопасно:

- deployment ещё не меняется;
- можно несколько раз перепроверить раскладку.

Проверка:

- каждый env file просмотрен на предмет лишних переменных;
- `.env.shared` содержит только действительно shared config;
- секреты не размножены без необходимости.

### Волна 1. Shared + low-risk service-scoped config

Цель:

- вынести низкорисковый config, не затрагивая критичные secrets.

Переносить:

- `PUBLIC_DOMAIN`
- `LICENSE_AUTH_DOMAIN`
- `ACCOUNT_MANAGER_DOMAIN`
- `PUBLIC_BASE_URL`
- `ACCOUNT_MANAGER_PORT`
- `ACCOUNT_MANAGER_CORS_ORIGINS`
- `LICENSE_AUTH_LOGIN_TITLE`
- `CONTROL_LEGACY_SHEETS_*`
- другие low-risk flags из ownership map

Изменения в compose:

- подключить `.env.shared`;
- подключить `.env.autolead`, `.env.license_auth`, `.env.account_manager`, `.env.caddy`;
- пока оставить старый `.env` как fallback только на время этой волны, если нужен безопасный переход.

Порядок перезапуска:

1. `autolead_bot`
2. `license_auth`
3. `account_manager`
4. `caddy`

Проверка после волны:

- все контейнеры healthy;
- dashboard и основные домены отвечают;
- `AccountManager` открывается;
- `license_auth` health работает.

### Волна 2. Service-scoped non-auth secrets

Цель:

- вынести partner/business и AI/provider keys по сервисам, не трогая основной auth boundary.

Переносить:

- `LEADSU_*`
- `LOVKO_*`
- `MFO_DOMAIN`
- `TELEGRAM_*`
- `DEEPSEEK_API_KEY`
- `FREELMAPI_API_KEY`
- `OPENROUTER_API_KEY`
- `CLOSEROUTER_API_KEY`

Куда:

- в `.env.autolead`
- либо в отдельный integrations/AI surface, если решите дробить ещё сильнее

Порядок перезапуска:

1. `autolead_bot`

Проверка после волны:

- partner integrations не деградировали;
- Telegram сценарии живы;
- AI/tooling сценарии не падают.

### Волна 3. Auth separation без rotation

Цель:

- разнести auth-related переменные по сервисам, пока ещё не ротируя их значения.

Переносить:

- `AUTH_MODE`
- `EXTERNAL_AUTH_*`
- `LICENSE_AUTH_*`
- `SESSION_SECRET_KEY` только после отдельного решения, должен ли он оставаться shared
- perimeter hashes (`ACCOUNT_MANAGER_BASIC_AUTH_*`, `AI_AGENT_BASIC_AUTH_*`) в `.env.caddy`

Самый чувствительный вопрос:

- `SESSION_SECRET_KEY`

Нужно отдельно решить:

1. Это намеренно shared между `autolead_bot` и `account_manager`?
2. Или это historical coupling, которое лучше разорвать?

Если ответа пока нет:

- на этой волне переносить переменную можно, но без разделения значения;
- то есть оставить её общей, но уже явно документированной.

Порядок перезапуска:

1. `license_auth`
2. `autolead_bot`
3. `account_manager`
4. `caddy`

Проверка после волны:

- login-flow работает;
- external auth verify не сломан;
- `AccountManager` middleware работает;
- публичные домены ведут себя ожидаемо.

### Волна 4. Cleanup и удаление legacy общего `.env`

Цель:

- перестать зависеть от одного общего env surface.

Что сделать:

- удалить из compose подключение старого общего `.env`, если временно оставляли fallback;
- убрать drift-переменные или задокументировать их окончательное назначение;
- минимизировать `.env.shared`.

Порядок перезапуска:

1. `autolead_bot`
2. `license_auth`
3. `account_manager`
4. `caddy`

Проверка после волны:

- ни один сервис не зависит скрыто от legacy `.env`;
- `.env.shared` действительно мал и не содержит лишних secrets;
- drift вокруг `ACCOUNT_MANAGER_BASIC_AUTH_*` устранён одним из двух способов:
  - либо переменные реально используются,
  - либо удалены.

## Diff

### Целевая миграция compose

```diff
autolead_bot:
  env_file:
-   - path: .env
+   - path: .env.shared
+   - path: .env.autolead
```

```diff
license_auth:
  env_file:
-   - path: .env
+   - path: .env.shared
+   - path: .env.license_auth
```

```diff
account_manager:
  env_file:
-   - path: .env
+   - path: .env.shared
+   - path: .env.account_manager
```

```diff
caddy:
+ env_file:
+   - path: .env.shared
+   - path: .env.caddy
```

Почему это безопасно:

- сначала переносится low-risk config;
- auth и perimeter secrets не трогаются на первом шаге;
- separation и rotation разведены по разным волнам;
- после каждой волны есть отдельный restart and verify cycle.

## Риски

- Самый опасный риск: совместить separation и rotation в одну волну.
- Второй риск: преждевременно разделить `SESSION_SECRET_KEY`, если он реально shared по контракту.
- Третий риск: оставить hidden dependency на старом `.env` и обнаружить её только после cleanup.

## Проверка после исправления

Для каждой волны нужен свой check-list.

Минимум:

1. Контейнеры healthy.
2. Public domains отвечают.
3. Login/auth flows работают.
4. Partner integrations и AI/tooling не деградировали там, где это относится к волне.
5. После cleanup больше нет скрытой зависимости от legacy `.env`.

## Дополнительные улучшения

- После separation можно уже безопаснее делать rotation wave-by-wave.
- Следующий зрелый шаг — увести `Critical` secrets из env files в отдельный managed secret layer.
