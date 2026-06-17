# AccountManager backend scaffold

Теги: #сущность

## Тип

Модуль / backend scaffold

## Где находится

`remote_server_snapshot/AccountManager/*`

## Роль в системе

Восстанавливает самодостаточную структуру AccountManager snapshot: конфиг, SQLAlchemy models, роутеры, сервисы и базовый dashboard. Без этого `api/main.py` ссылался на отсутствующие модули.

## Входы

- `SESSION_SECRET_KEY`
- `ENCRYPTION_KEY`
- `DB_PATH`
- запросы к `/api/telegram/*`, `/api/google/*`, `/api/social/*`

## Выходы

- таблицы `telegram_accounts`, `google_accounts`, `social_accounts`, `proxies`, `accounts`
- backend endpoints по ТЗ
- базовый HTML dashboard

## Зависимости

- [[AccountManager]]
- [[Authentication]]

## Типовые сбои или риски

- live Telethon/Playwright flow в этом snapshot пока scaffold-only;
- реальная браузерная автоматизация потребует полный runtime и секреты.
