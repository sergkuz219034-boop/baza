# Runtime Inspector

## Что это
Admin-only read-only endpoint и dashboard-блок для диагностики live runtime.

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

## Почему admin-only
Runtime Inspector показывает инфраструктурное состояние и owner-активность. Обычный `user` не должен видеть системную карту и чужие runtime-признаки.

## Связанные файлы
- `/root/TrafficHub/api/routers/system.py`
- `/root/TrafficHub/dashboard/index.html`
- `/root/TrafficHub/dashboard/app.js`

## Связанные заметки
- [[Runtime doctor]]
- [[Job Queue]]

