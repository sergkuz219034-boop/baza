# Runtime Inspector

## Что это
Admin-only read-only endpoint и dashboard-блок для диагностики live runtime.

## Где в интерфейсе
`Admin панель` -> карточка `Диагностика runtime`.

Раньше блок временно находился в `Настройки`, но это было неудобно: пользователь ожидает системную диагностику именно в admin-разделе. После commit `dad9bde3b` блок перенесён в `Admin панель`.

## Endpoint
`GET /api/system/runtime-inspector`

Доступ: только `admin`.

## Что показывает
- текущий commit;
- environment;
- PostgreSQL health;
- Redis health;
- активные jobs по owner;
- размеры очередей;
- наличие диагностических утилит.

В той же admin-only карточке находится `История задач`, которая читает [[Job Timeline]].

После commit `5d9fc210a` admin-раздел вызывает Runtime Inspector автоматически при открытии `Admin панель`, а не только по кнопке `Проверить runtime`.

## Commit в hotfix-deploy

Runtime Inspector читает commit через общий helper в `/root/TrafficHub/api/routers/system.py`.

При обычной сборке используется `git rev-parse HEAD`.

При hotfix-деплое через `docker cp` используется marker [[TrafficHub deployed commit marker]]: `/app/.deploy_commit`. Это нужно, потому что `.git` внутри контейнера может оставаться stale, хотя live-код уже скопирован.

## Почему admin-only
Runtime Inspector показывает инфраструктурное состояние и owner-активность. Обычный `user` не должен видеть системную карту и чужие runtime-признаки.

## Связанные файлы
- `/root/TrafficHub/api/routers/system.py`
- `/root/TrafficHub/dashboard/index.html`
- `/root/TrafficHub/dashboard/app.js`

## Связанные заметки
- [[Runtime doctor]]
- [[Job Queue]]
