# 2026-06-23 Maintenance mode host-container config drift

## Симптом

- В live UI пользователь видел обычный интерфейс TrafficHub вместо полноэкранного баннера `Тех работы`.
- Host-проверка `/root/TrafficHub` показывала `maintenance_mode=True`, но реальный контейнер `autolead_server_bot` отдавал `maintenance_mode=False`.

## Зона системы

- live repo: `/root/TrafficHub`
- контейнер: `autolead_server_bot`
- frontend: `dashboard/app.js`, `dashboard/index.html`
- backend endpoint: `api/routers/settings.py`, `/api/settings/maintenance-mode`
- runtime config: `/app/data/runtime/secrets/config.json`
- volume на host: `/root/TrafficHub/data/runtime/secrets/config.json`

## Гипотеза

- Флаг был включён не в том runtime-источнике: host Python прочитал один config context, а UI работает через backend внутри контейнера.

## Проверка

- Host: `python3 ... load_config(force_reload=True)` показал `maintenance_mode=True`.
- Container: `docker exec autolead_server_bot ... load_config(force_reload=True)` показал `maintenance_mode=False`.
- После записи через контейнерный `save_config()` повторная проверка внутри контейнера показала `maintenance_mode=True`.

## Наблюдение

- `dashboard/app.js` показывает overlay только если `/api/settings/maintenance-mode` возвращает `enabled=true` и текущая роль не `admin`.
- Нельзя считать host-side запуск `python3` достаточной проверкой UI-состояния, если рабочий backend обслуживается контейнером.
- Live health подтверждён через контейнерный порт `8080`: `/api/health` вернул `status=ok`.

## Вывод

- Для live-техработ каноничная проверка и запись должна идти через backend/container runtime:
  - предпочтительно API `/api/settings/maintenance-mode`;
  - допустимо `docker exec autolead_server_bot ... save_config()` при аварийной ручной операции.
- Проверка только из `/root/TrafficHub` без контейнера может дать ложное ощущение, что техработы включены.

## Следующий шаг

- В [[02_Код/Эксплуатация/Развёртывание]] или отдельном плейбуке закрепить правило: maintenance mode проверяется по контейнерному runtime и UI/API, а не только по host repo.
