# Docker

## Файлы

| Файл | Описание |
|------|----------|
| `Dockerfile` | python:3.11-slim + Playwright Chromium |
| `docker-compose.yml` | Сервис `autolead_bot` + опциональный `caddy` |
| `docker-compose.local.yml` | Локальный Caddy override |
| `docker-entrypoint.sh` | Создание папок data/secrets + exec |
| `deploy/Caddyfile` | Reverse proxy + HTTPS |
| `deploy/Caddyfile.local` | Локальный Caddy config |

## Порты

| Сервис | Порт |
|--------|------|
| TrafficHub (Autolead) | 8080 |
| Caddy (опционально) | 80 + 443 |

## Режимы профиля Caddy

### local
```bash
CADDY_PROFILE=local docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

### public
```bash
CADDY_PROFILE=public docker compose up -d
```

## Запуск

```bash
docker compose up -d
```

## Связанное

- [[06-Deployment/Windows|Windows Setup]]
- [[03-API/WebSocket|WebSocket]]
