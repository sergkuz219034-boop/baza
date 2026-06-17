# Authentication

Теги: #архитектура

## Подтверждённые механизмы

### Dashboard

- session principal в `api.authz`
- HTTP Basic через `validate_user(...)`
- дополнительный runtime gate через `AutoleadAccess` для owner-scoped Autolead операций

### TrafficHub

- session principal
- HTTP Basic
- локальный JWT по `settings.secret_key`
- внешний bearer token при `is_external_auth_enabled()`

Фактически это значит, что авторизация состоит из двух слоёв:

- identity / role check
- ownership / tenant scope check в самих роутерах и query helpers

### AccountManager

- bearer/JWT через `SESSION_SECRET_KEY`
- токен ищется в `Authorization`, query `token`, cookie `access_token`

## Почему auth многослойный

- legacy runtime начинался с локального логина;
- позже появился внешний auth и отдельные сервисы;
- часть интеграций требует session-поведение, часть bearer.

## Риски

- несколько token surface в одном deployment;
- drift между reverse proxy и приложением;
- высокая цена ошибок в `SESSION_SECRET_KEY` и `EXTERNAL_AUTH_*`.
- drift между legacy runtime-path значениями в `config.json` и фактическим storage layout.

## Runtime secrets note

После актуальной серверной схемы runtime-конфиг и кэши лежат в `data/runtime/secrets/`.

Старые значения вида `secrets/service_account.json` теперь считаются legacy-compatible, но не каноническими.

## Смежные страницы

- [[Authorization]]
- [[Security]]
