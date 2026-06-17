# Architecture Map: Current Server

Дата: 2026-06-01
Источник фактов:

- live server `/root/TrafficHub`
- `remote_server_snapshot`
- `remote_files`

## Анализ

### Общая структура репозитория

По live server подтверждён следующий top-level контур:

- `main.py`
- `api/*`
- `config/*`
- `services/*`
- `utils/*`
- `modules/*`
- `traffic_hub/*`
- `license_auth/*`
- `AccountManager/*`
- `dashboard/*`
- `deploy/*`
- `tests/*`
- `tools/*`
- `wiki/*`
- `docs/*`
- `data/*`
- `secrets/*`

Это не “один backend”, а фактически монорепо из нескольких подсистем.

### Подсистема 1. Autolead runtime

Точка входа:

- `main.py`

Основные зависимости:

- `config.settings`
- `services.leads_service`
- `utils.database`
- `utils.control_store`
- `utils.control_sync`

Назначение:

- scheduler;
- сбор лидов;
- выгрузка в Google Sheets;
- рассылка через Playwright;
- локальный runtime и файловое логирование.

### Подсистема 2. Autolead Dashboard / API

Точка входа:

- `api/server.py`

Назначение:

- FastAPI dashboard;
- session/auth слой для Autolead;
- HTTP API и WebSocket;
- подключение роутеров `jobs`, `leads`, `stats`, `settings`, `offers`, `system`, `debug`, `avito`, `control`.

Ключевая особенность:

- этот слой одновременно поднимает Dashboard и встраивает `traffic_hub` через `register_traffic_hub(...)`.

### Подсистема 3. TrafficHub

Точка входа:

- `traffic_hub/app.py`

Назначение:

- отдельный FastAPI-контур внутри того же репозитория;
- собственные роутеры:
  - `auth`
  - `integrations`
  - `leads`
  - `offers`
  - `finance`
  - `messengers`
  - `funnels`
  - `tracking`
  - `postbacks`
  - `stats`
  - `tools`
- собственный WebSocket `/traffic-ws` и `/ws`;
- собственные migrations и DB engine.

### Подсистема 4. License Auth

Точка входа:

- `license_auth.app:app`

Назначение:

- внешний auth/issuer слой;
- интеграция с `EXTERNAL_AUTH_*` / `LICENSE_AUTH_*`.

### Подсистема 5. AccountManager

Точка входа:

- `AccountManager/api/main.py`

Назначение:

- отдельный сервис для account/proxy/content management;
- свой UI и data layer;
- отдельный docker build context;
- доп. `tg-ws-proxy`.

### Подсистема 6. Infra / delivery

Файлы:

- `docker-compose.yml`
- `deploy/Caddyfile`
- `.github/workflows/*`
- `tools/windows_*`

Назначение:

- контейнеризация;
- reverse proxy;
- публикация доменов;
- локальные Windows launch/install tooling.

## Причина

### Архитектурная особенность 1. В одном репозитории живут два разных web-контура

- `api/server.py` + Autolead Dashboard
- `traffic_hub/app.py` + TrafficHub API

Они связаны, но не тождественны.

Это объясняет часть исторической путаницы:

- разные наборы роутеров;
- разные config surfaces;
- разные DB contexts;
- неполный `remote_files` легко создаёт ложное впечатление “сломанных импортов”.

Критичность: `Medium` как architectural risk

### Архитектурная особенность 2. Два независимых settings-контекста

Подтверждены:

- `config/settings.py`
- `traffic_hub/config/settings.py`

Они решают разные задачи:

- `config/settings.py` — Autolead runtime, secrets cache, Sheets, session secret, local control store;
- `traffic_hub/config/settings.py` — Pydantic settings для отдельного API/DB/auth слоя.

Это объясняет, почему конфигурационные проблемы и auth drift сложно расследуются “одним взглядом”.

Критичность: `Medium`

### Архитектурная особенность 3. Несколько auth boundary в одном проекте

Подтверждены:

- session auth в `api/server.py`
- auth / JWT secrets в `traffic_hub/config/settings.py`
- `license_auth/*`
- `AccountManager/api/main.py`

Это не обязательно дефект, но это сильный источник drift:

- разные токены;
- разные secret keys;
- разные perimeter assumptions;
- reverse proxy может защищать контур не так, как ожидает приложение.

Критичность: `Medium`

## План исправления

На этом этапе архитектуру менять не нужно. Правильный шаг — использовать карту как ограничитель для расследований и фиксов:

1. Любой runtime-баг сначала относить к конкретной подсистеме.
2. Не анализировать `remote_files` как полный source of truth.
3. Любой auth/config дефект проверять минимум в трёх слоях:
   - app config
   - reverse proxy
   - deployment env

## Diff

Код проекта не менялся.

Добавлен только документ:

- `05 Решения/2026-06-01 architecture map current server.md`

Почему это безопасно:

- карта не меняет систему;
- она снижает риск ложной диагностики и неправильного patching.

## Риски

- Если продолжать воспринимать репозиторий как “один backend”, легко снова смешать:
  - Autolead runtime
  - Autolead dashboard
  - TrafficHub API
  - AccountManager
  - License Auth
- Это уже приводило к переоценке `remote_files` и частично искажало ранние выводы.

## Проверка после исправления

Фактически проверка уже выполнена через:

- live server directory listing;
- top-level file inventory;
- чтение:
  - `requirements.txt`
  - `main.py`
  - `api/server.py`
  - `traffic_hub/app.py`
  - `config/settings.py`
  - `traffic_hub/config/settings.py`

## Дополнительные улучшения

- Позже стоит сделать “ownership map” по подсистемам:
  - какой контейнер
  - какая БД
  - какой auth boundary
  - какой public domain
- Для дальнейших расследований полезно поддерживать синхронизируемый полный snapshot сервера, а не частичные зеркала `remote_files` / `remote_server_snapshot`.
