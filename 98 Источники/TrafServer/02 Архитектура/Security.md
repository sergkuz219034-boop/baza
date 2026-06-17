# Security

Теги: #архитектура

## Подтверждённые сильные стороны

- loopback binding для внутренних сервисов в compose;
- reverse proxy через Caddy;
- bcrypt для паролей пользователей;
- session/cookie с `secure` и `httponly` для AccountManager;
- owner-scoped data access.

## Подтверждённые риски

- секреты сильно завязаны на `.env`;
- несколько auth boundary в одном deployment;
- legacy Google Sheets compatibility всё ещё присутствует в `license.py`;
- Caddy защищает AI perimeter basic auth, но AccountManager basic auth по текущему `Caddyfile` не включён.

## Почему это спорное место

Система одновременно мигрирует с legacy control plane и поддерживает новые login-scoped данные. Это снижает риск потери обратной совместимости, но расширяет поверхность ошибок.

## Смежные страницы

- [[Authentication]]
- [[Infrastructure]]
- [[Known Issues]]
