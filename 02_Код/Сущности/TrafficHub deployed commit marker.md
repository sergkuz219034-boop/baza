# TrafficHub deployed commit marker

## Что это

Файл `/app/.deploy_commit` внутри контейнера `autolead_server_bot` фиксирует commit, который реально применён в runtime после hotfix-деплоя.

## Зачем нужен

Рабочая модель TrafficHub допускает быстрый server hotfix через копирование изменённых файлов в контейнер. В таком сценарии `.git` внутри `/app` может оставаться на старом commit, хотя код уже обновлён.

Без marker admin-блок `Обновление из GitHub` показывает stale `current_commit` и создаёт ложное ощущение, что сервер не обновлён.

## Где используется

- `/root/TrafficHub/api/routers/system.py`
- endpoint `GET /api/system/git-status`
- endpoint `GET /api/system/runtime-inspector`
- dashboard-блок `Обновление из GitHub`
- dashboard-блок `Runtime Inspector`

## Правило

После hotfix-копирования файлов в live container нужно записать короткий commit:

```bash
git rev-parse --short HEAD > /tmp/deploy_commit
docker cp /tmp/deploy_commit autolead_server_bot:/app/.deploy_commit
```

Если worker использует тот же код, marker также кладётся в `traffichub_worker:/app/.deploy_commit`.

## Ограничение

Marker не заменяет git history. Источник истории остаётся server repo `/root/TrafficHub` и GitHub. Marker нужен только для корректной runtime-индикации после hotfix-deploy.

## Связанные заметки

- [[Runtime Inspector]]
- [[Runtime doctor]]
- [[Fast debug loop]]
