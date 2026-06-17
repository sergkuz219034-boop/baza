# remote_server_snapshot

Снимок серверного окружения и точек входа.

## Что здесь лежит

- [AccountManager/README.md](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/AccountManager/README.md) — отдельный сервис AccountManager
- [main.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/main.py) — серверный вход
- [docker-compose.yml](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/docker-compose.yml) — live compose схема
- [config.settings.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/config.settings.py) — конфиг сервера
- [deploy/Caddyfile](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/deploy/Caddyfile) — reverse proxy
- [traffic_hub/worker.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/traffic_hub/worker.py) — worker-process
- [api](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api) — серверные routers
- [services](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services) — сервисный слой
- [utils](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils) — общие утилиты
- [traffic_hub/README.md](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/traffic_hub/README.md) — встроенный контур TrafficHub
- [api/README.md](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/README.md) — серверные routers
- [services/README.md](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/README.md) — сервисный слой
- [utils/README.md](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/README.md) — общие утилиты

## Как использовать

1. Для понимания live-схемы открой `docker-compose.yml`.
2. Для маршрутизации и внешнего доступа смотри `deploy/Caddyfile`.
3. Для worker/health — `traffic_hub/worker.py`.
4. Для AccountManager начинай с `AccountManager/README.md`.
