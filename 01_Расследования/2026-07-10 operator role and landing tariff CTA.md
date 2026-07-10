# 2026-07-10 operator role and landing tariff CTA

## Симптом

Нужна отдельная роль `operator` с максимально ограниченным функционалом для рабочей обработки лидов. На публичном лендинге кнопки `Выбрать` в тарифах должны вести не в авторизацию, а в Telegram продавца.

## Зона системы

- `utils/access.py`
- `api/authz.py`
- `api/autolead_access.py`
- `api/routers/settings.py`
- `api/routers/offers.py`
- `api/routers/settings_maintenance.py`
- `api/routers/system.py`
- `traffic_hub/models/database.py`
- `traffic_hub/authz.py`
- `dashboard/app.js`
- `dashboard/index.html`
- `dashboard/landing.html`

## Гипотеза

Старый alias `operator = user` слишком широкий: оператор получает возможности обычного пользователя, включая настройки, офферы и запуск Autolead jobs. Для рабочего режима нужна отдельная роль ниже `user`.

## Проверка

- Код role-rank в `utils/access.py` проверен и изменён на `operator < user < admin`.
- PostgreSQL enum `userrole` на live расширен значением `operator`.
- Frontend проверен на hash-navigation и кнопки `data-user-action`.
- Live app/worker пересобраны из `/root/TrafficHub`.
- `/api/health` после deploy вернул `{"status":"ok"}`.
- Regression tests:
  - `tests/test_access.py`
  - `tests/test_auth_roles.py`
  - `tests/test_license_auth.py`
  - `tests/test_license_key_security.py`
  - `tests/test_traffic_tenant_isolation.py`
  - `tests/test_landing_routes.py`
  - `tests/test_settings_license_accounts.py`
  - `tests/test_settings_import_export.py`
  - `tests/test_offers_import_export.py`
  - `tests/test_jobs_router.py`
  - `tests/test_zarplata_router.py`
  - `tests/test_system_backups.py`
  - `tests/test_settings_maintenance.py`
  - `tests/test_autolead_access.py`

## Наблюдение

- `operator` больше не алиас `user`.
- `require_user` является порогом для изменения настроек, офферов, maintenance, system actions и jobs.
- `require_autolead_operator` используется как read/basic lead access threshold.
- UI скрывает user-level разделы и возвращает оператора на `#leads`, если запрещённая вкладка открыта прямым hash.
- Кнопки тарифов `Выбрать` на лендинге ведут на `https://t.me/sergkuz2190`.

## Вывод

Роль `operator` стала отдельным минимальным рабочим режимом. Её нельзя снова маппить в `user`, иначе оператор получит доступ к настройкам и запуску jobs.

## Следующий шаг

Если потребуется расширять операторский функционал, добавлять точечные permissions, а не повышать роль до `user`.
