# Авторизация

Файл: `api/authz.py` (139 строк)

## Уровни доступа

| Роль | Права |
|------|-------|
| `admin` | Полный доступ |
| `operator` | Ограниченные деструктивные операции |
| `unauthenticated` | Только health/public endpoints |

## Методы аутентификации

1. **Session cookie** — для браузера (Starlette SessionMiddleware)
2. **HTTP Basic Auth** — для API и WebSocket

## RBAC

```mermaid
graph LR
    A[Request] --> B{Session?}
    B -->|Да| C[Check role]
    B -->|Нет| D{Basic Auth?}
    D -->|Да| C
    D -->|Нет| E[anon]
    C --> F[Allow/Deny]
```

## Связанное

- [[материалы/документы/TrafficHub-obsidian/05-Configuration/Config|Конфигурация]]
- [[материалы/документы/TrafficHub-obsidian/04-Database/control|control.db]]
