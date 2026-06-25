# БАГ-010: не было глобального режима техработ для user

## Симптом

В dashboard не было штатного способа быстро закрыть панель для всех пользователей `user` на время работ, не затрагивая admin-доступ.

## Зона системы

- `api/routers/settings.py`
- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/style.css`
- глобальный `config.json`

## Гипотеза

Режим техработ должен жить не в user-scoped профиле, а в глобальном runtime-конфиге, иначе admin включит флаг только для себя.

## Проверка

- Проверена модель `load_config()` / `save_config()` в `services/leads_service.py`.
- При активном `bind_current_username(...)` обычный `save_config()` пишет в `control_user_app_configs`, а не в общий локальный `config.json`.
- Для глобального флага используется отдельный endpoint `/api/settings/maintenance-mode`, который сохраняет значение без user-scoped override.

## Наблюдение

Реализация сделана так:

- `GET /api/settings/maintenance-mode` возвращает глобальный state;
- `PATCH /api/settings/maintenance-mode` доступен только admin;
- в `Admin панели` появился тумблер сохранения режима;
- у всех `user` поверх dashboard показывается fullscreen overlay `Тех работы`;
- admin overlay не блокирует.
- с `2026-06-24` текст баннера больше не редактируется ни в UI, ни через API: backend принудительно хранит только `Тех работы`.

## Вывод

Канон для техработ:

- флаг должен быть глобальным;
- переключатель должен быть только у admin;
- user должен блокироваться на уровне UI сразу после опроса состояния;
- admin должен сохранять доступ для выключения режима и диагностики.

## Следующий шаг

- если понадобится почти мгновенное срабатывание без polling, вынести maintenance-state в существующий status websocket payload.
