# traffic_hub

Основной встроенный контур TrafficHub.

## Что здесь важно

- [app.py](C:/Users/Арт/Desktop/TrafServer/remote_files/traffic_hub/app.py) — регистрация routers и websocket
- [api/deps.py](C:/Users/Арт/Desktop/TrafServer/remote_files/traffic_hub/api/deps.py) — dependencies и auth
- [api/ownership.py](C:/Users/Арт/Desktop/TrafServer/remote_files/traffic_hub/api/ownership.py) — owner-scoped helpers
- [models/database.py](C:/Users/Арт/Desktop/TrafServer/remote_files/traffic_hub/models/database.py) — модели и база
- [migrations.py](C:/Users/Арт/Desktop/TrafServer/remote_files/traffic_hub/migrations.py) — миграции

## Как читать

1. Начинай с `app.py`.
2. Потом смотри `api/deps.py` и `api/ownership.py`.
3. Для данных переходи в `models/database.py` и `alembic/versions`.
