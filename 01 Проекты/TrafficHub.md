# TrafficHub

## Статус

Активный технический проект для сопровождения через серверный репозиторий и локальную wiki.

## Что подтверждено

- `C:\Users\Арт\Desktop\TrafServer` не является локальным git-клоном приложения. Это отдельный workspace для wiki, SSH-утилит и server-side расследований.
- Канонический mutable-репозиторий приложения живёт на сервере в `/root/TrafficHub`.
- В `C:\Users\Арт\Desktop\TrafServer\remote_files\traffic_hub\app.py` регистрируются HTTP-роутеры `auth`, `finance`, `funnels`, `integrations`, `leads`, `messengers`, `offers`, `postbacks`, `stats`, `tools`, `tracking`.
- В том же `app.py` подняты websocket endpoints `/traffic-ws` и `/ws`.
- В `C:\Users\Арт\Desktop\TrafServer\remote_files\traffic_hub\api\deps.py` есть несколько режимов аутентификации:
  - внешний token flow;
  - session principal;
  - HTTP Basic;
  - JWT через `OAuth2PasswordBearer`.
- В `C:\Users\Арт\Desktop\TrafServer\remote_files\tests\test_traffic_tenant_isolation.py` есть проверка owner-scope поведения для `offers`, `leads`, `finance`, `messengers`, `funnels`, `stats`, `tracking`.

## Где лежат материалы проекта

### Основной workspace

- `C:\Users\Арт\Desktop\TrafServer`
- Назначение:
  - wiki;
  - SSH и remote debug;
  - read-only зеркала и snapshots;
  - плейбуки и архитектурные заметки.

### Runtime

- `C:\Users\Арт\Desktop\TrafServer_runtime`
- Сейчас подтверждено только одно содержимое: `paramiko_runtime`.
- По `C:\Users\Арт\Desktop\TrafServer\tools\local_ssh.py` этот runtime используется как один из candidate paths для загрузки `paramiko`.
- Вывод: `TrafServer_runtime` сейчас выглядит как технический runtime для SSH-утилит, а не как исходники TrafficHub.

### Storage

- `C:\Users\Арт\Desktop\TrafServer_storage`
- Там лежат локальные state и data артефакты:
  - `accounts.db`
  - `autolead.db`
  - `control.db`
  - `adspower_local_state.json`
  - `rabota_tokens.json`

## Точки входа

### Для кода и архитектуры

- `C:\Users\Арт\Desktop\TrafServer\remote_files\traffic_hub\app.py`
- `C:\Users\Арт\Desktop\TrafServer\remote_files\traffic_hub\api\deps.py`
- `C:\Users\Арт\Desktop\TrafServer\remote_files\api\routers`
- `C:\Users\Арт\Desktop\TrafServer\remote_files\tests\test_traffic_tenant_isolation.py`

### Для server-side работы

- `C:\Users\Арт\Desktop\TrafServer\tools\local_ssh.py`
- `C:\Users\Арт\Desktop\TrafServer\tools\remote_exec.py`
- `C:\Users\Арт\Desktop\TrafServer\tools\push_fix.py`
- `C:\Users\Арт\Desktop\TrafServer\tools\ssh_key_readiness.py`

## Как реально менять проект

1. Подключение к серверу.
2. Работа в `/root/TrafficHub`.
3. Проверка поведения на сервере.
4. Commit и push из серверного repo.
5. После этого обновление локальной wiki в `TrafServer` и этой базы Obsidian.

## Что важно понимать сразу

- Локальная папка `TrafServer_runtime` не даёт полной карты приложения.
- Если строить wiki только по `TrafServer_runtime`, получится искажённая картина, потому что там сейчас виден только runtime для `paramiko`.
- Для нормального заполнения базы по `TrafficHub` надо опираться в первую очередь на:
  - `remote_files`;
  - `remote_server_snapshot`;
  - `tools`;
  - server runtime и repo на сервере.

## Риски и ограничения

- Старые локальные зеркала не равны live-серверу без сверки.
- Runtime и storage содержат технические артефакты, но не заменяют исходный код.
- Любые архитектурные выводы по приложению нужно подтверждать либо кодом из `remote_files`, либо сервером.

## Что заполнить дальше

1. Карта роутеров `TrafficHub` по папке `remote_files`.
2. Карта auth/authz и owner-scoped модели.
3. Карта БД и ключевых таблиц.
4. Плейбук: как безопасно проверять сервер и синхронизировать знания в wiki.
