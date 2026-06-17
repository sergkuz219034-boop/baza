# AccountManager snapshot

Снимок отдельного сервиса AccountManager.

## Что здесь лежит

- `api/` — API сервис
- `database/` — модели и подключение к БД
- `services/` — бизнес-логика
- `dashboard/` — frontend части
- `chrome-extension/` — браузерное расширение
- `scheduler.py` — планировщик
- `tests_smoke.py` — smoke-check

## Как читать

1. Начинай с `api/main.py`.
2. Потом `database/models.py`.
3. Дальше переходи в `services/` и `dashboard/`.
