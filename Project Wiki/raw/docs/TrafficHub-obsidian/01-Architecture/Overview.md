# Архитектура

## Общая схема

Монолитное приложение — единый Python-процесс, содержащий:
- **FastAPI** сервер (порт 8080)
- **Планировщик** задач (фоновый поток)
- **WebSocket** менеджер
- **Три SQLite базы**

## Слои

```
┌─────────────────────────────────────┐
│           main.py (entry)           │
├─────────────────────────────────────┤
│          services/ (оркестрация)     │
│  leads_service.py, stats_service.py  │
├─────────────────────────────────────┤
│   modules/ (интеграции)              │
│  rabota_api, sheets_sync, vbiv_bot  │
├─────────────────────────────────────┤
│   utils/ (инфраструктура)            │
│  database, control_store, license    │
├─────────────────────────────────────┤
│   api/ (веб-слой)                    │
│  server, routers, authz, ws_manager  │
└─────────────────────────────────────┘
```

## Ключевые принципы

- **Local-first**: данные хранятся локально в SQLite. Google Sheets — только экспорт.
- **Thread-safety**: `threading.Lock()` вокруг shared state (config cache, WS connections).
- **Graceful shutdown**: SIGTERM → `stop_event.set()` → потоки проверяют `is_stop_requested()`.
- **Hot-reload config**: перечитывается каждые 30 секунд; API — с TTL-кэшем 5 секунд.
- **MSK timezone** (UTC+3) везде.

## Связанное

- [[DataFlow]]
- [[Scheduler]]
- [[Scoring]]
- [[04-Database/Schema|Схема БД]]
