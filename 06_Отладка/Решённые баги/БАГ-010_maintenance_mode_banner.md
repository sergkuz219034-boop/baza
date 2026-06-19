# БАГ-010: не было глобального режима техработ для user

## Симптом

В dashboard не было штатного способа быстро закрыть панель для всех пользователей `user` на время работ, не затрагивая admin-доступ.

## Зона системы

- `api/routers/system.py`
- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/style.css`
- глобальный `config.json`

## Гипотеза

Режим техработ должен жить не в user-scoped профиле, а в глобальном runtime-конфиге, иначе admin включит флаг только для себя.

## Проверка

- Проверена модель `load_config()` / `save_config()` в `services/leads_service.py`.
- При активном `bind_current_username(...)` обычный `save_config()` пишет в `control_user_app_configs`, а не в общий локальный `config.json`.
- Для глобального флага добавлен отдельный endpoint в `system`-роутер, который читает `load_config_local()` и сохраняет через `save_config()` без user-bind контекста.

## Наблюдение

Реализация сделана так:

- `GET /api/system/maintenance` возвращает глобальный state;
- `PATCH /api/system/maintenance` доступен только admin;
- в `Admin панели` появился тумблер сохранения режима;
- у всех `user` поверх dashboard показывается fullscreen overlay `Тех работы`;
- admin overlay не блокирует.

## Вывод

Канон для техработ:

- флаг должен быть глобальным;
- переключатель должен быть только у admin;
- user должен блокироваться на уровне UI сразу после опроса состояния;
- admin должен сохранять доступ для выключения режима и диагностики.

## Следующий шаг

- если понадобится почти мгновенное срабатывание без polling, вынести maintenance-state в существующий status websocket payload.
