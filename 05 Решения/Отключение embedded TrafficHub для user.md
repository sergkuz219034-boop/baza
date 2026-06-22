# Отключение embedded TrafficHub для user

## Проблема

Роль `user` не должна видеть и использовать embedded TrafficHub CRM. Ранее похожая модель уже была для Account Manager.

## Контекст

TrafficHub живёт внутри общего dashboard рядом с Autolead. UI-скрытие само по себе недостаточно, потому что API `/traffic-api/*` остаётся доступным при прямом запросе.

## Решение

Сделано два уровня защиты:

- `dashboard/app.js` скрывает и блокирует sidebar-раздел `TrafficHub` для всех не-admin пользователей.
- `traffic_hub/api/deps.py::require_operator()` для embedded CRM surface теперь требует `ROLE_ADMIN`, а не `ROLE_USER`.

## Последствия

- `admin` продолжает видеть и использовать embedded TrafficHub.
- `user` видит Autolead и свои рабочие настройки, но не TrafficHub CRM.
- Прямой обход через `/traffic-api/*` для `user` должен получать `403`.

## Альтернативы

- Только UI-скрытие: отклонено, потому что не защищает backend.
- Полное удаление TrafficHub routes из приложения: отклонено, потому что admin всё ещё нужен доступ к CRM.
- Отдельный feature flag: возможно позже, если потребуется включать TrafficHub выборочно для отдельных клиентов.
