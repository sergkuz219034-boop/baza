# 150.241.70.31

## Параметры доступа

- Host: `150.241.70.31`
- Login: `root`
- Password: хранится вне workspace; для локальных SSH-утилит используйте `TRAFSERVER_PASSWORD`

## Проверка подключения

- SSH-подключение подтверждено: сервер отвечает.
- Hostname: `TrafficHub.play2go.cloud`
- Рабочая директория после входа: `/root`
- Платформа: `Linux TrafficHub.play2go.cloud 6.8.0-111-generic x86_64 GNU/Linux`

## Локальные замечания

- Локальный `paramiko` runtime вынесен из Obsidian vault во внешнюю папку `C:\Users\Арт\Desktop\TrafServer_runtime\paramiko_runtime`, чтобы не ломать сканирование workspace в Obsidian.
- Корневые SSH-утилиты используют `TRAFSERVER_HOST`, `TRAFSERVER_USER`, `TRAFSERVER_PASSWORD` и при необходимости `TRAFSERVER_PARAMIKO_PATH`.

## Server repo

- Рабочий mutable repo TrafficHub на сервере: `/root/TrafficHub`
- Локальный clone больше не используется
- Локальный `TrafServer` хранит только wiki, SSH-утилиты и snapshots

## GitHub remote

- `origin`: `git@github.com:sergkuz219034-boop/TrafficHub.git`
- На 2026-06-11 подтверждены `git fetch origin` и `git push origin main` прямо с сервера.
- Для docs-only синхронизации безопасно использовался временный worktree, потому что основной `/root/TrafficHub` содержит незакоммиченные server-side изменения и не должен получать `pull` поверх грязного дерева.
