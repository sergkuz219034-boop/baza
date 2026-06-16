# API Overview

## Базовый URL

```
http://localhost:8080
```

## Документация

- Swagger: `http://localhost:8080/docs`
- WebSocket: `ws://localhost:8080/ws`

## Эндпоинты

| Группа | Роутер | Описание |
|--------|--------|----------|
| `GET /health` | system | Проверка здоровья |
| `GET /api/leads` | leads | Список лидов |
| `GET /api/stats` | stats | Статистика |
| `POST /api/jobs/run` | jobs | Запуск задачи |
| `GET /api/settings` | settings | Чтение конфига |
| `POST /api/offers` | offers | CRUD offers |
| `POST /api/avito/import` | avito | Импорт Avito |
| `GET /api/ws` | ws_manager | WebSocket |

## Авторизация

См. [[материалы/документы/TrafficHub-obsidian/03-API/Auth|Auth]]

## Связанное

- [[материалы/документы/TrafficHub-obsidian/03-API/Auth|Авторизация]]
- [[материалы/документы/TrafficHub-obsidian/03-API/Endpoints|Эндпоинты]]
- [[материалы/документы/TrafficHub-obsidian/03-API/WebSocket|WebSocket]]
