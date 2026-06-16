# WebSocket

Файл: `api/ws_manager.py` (94 строки)

## Endpoint

```
ws://localhost:8080/ws
```

## Назначение

- Трансляция логов в реальном времени
- Статус выполнения задач
- Push-уведомления дашборду

## Схема

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Logger
    Client->>FastAPI: WS Connect /ws
    FastAPI->>Client: Confirm
    Logger->>FastAPI: Log line
    FastAPI->>Client: {"type":"log","data":"..."}
    Logger->>FastAPI: Status update
    FastAPI->>Client: {"type":"status","data":{...}}
```

## Связанное

- [[03-API/Overview|API Overview]]
- [[06-Deployment/Docker|Docker]]
