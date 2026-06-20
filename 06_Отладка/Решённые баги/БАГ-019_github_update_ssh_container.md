# БАГ-019: обновление из GitHub падало внутри контейнера

## Статус

Решено на live-сервере.

## Симптом

В блоке `Обновление из GitHub` UI показывал:

```text
error: cannot run ssh: No such file or directory
fatal: unable to fork
```

## Причина

`/api/update` и `/api/git-status` выполняют git-команды внутри контейнера `autolead_server_bot`.

В контейнере:

- remote `/app` был `git@github.com:sergkuz219034-boop/TrafficHub.git`;
- был установлен `git`;
- не было `ssh`;
- не было отдельной настройки deploy key для runtime.

Дополнительно `/api/git-status` игнорировал ошибку `git fetch origin`, из-за чего UI мог показывать stale-состояние `origin/main`.

## Исправление

- В `Dockerfile` добавлен `openssh-client`.
- В `api/routers/system.py`:
  - если `GIT_UPDATE_TOKEN` задан, SSH remote переводится в HTTPS remote без записи токена в URL;
  - если токена нет, используется runtime deploy key `/app/secrets/github_ssh/traffichub_github` через `GIT_SSH_COMMAND`;
  - `/api/git-status` больше не игнорирует ошибку `fetch`.
- На live сервере deploy key помещён в `secrets/github_ssh/traffichub_github`. Эта папка находится в ignored runtime secrets, ключ не коммитится.

## Проверка

- После rebuild в контейнере есть `/usr/bin/ssh`.
- Внутри контейнера `system._run_git(["fetch", "origin"])` вернул `fetch_rc 0`.
- `HEAD` и `origin/main` совпали.

## Коммит

`320c05311 Fix dashboard refresh and GitHub update runtime`
