# Rabota.ru API

Файл: `modules/rabota_api.py` (~1100+ строк)

## Возможности

- OAuth2 with SHA-256 signed requests
- Automatic token refresh
- Server time skew correction
- VPN/proxy detection

## Основные методы

| Метод | Описание |
|-------|----------|
| `get_responses()` | Получение откликов на вакансии (пагинация) |
| `get_autofit_resumes()` | Автоподбор кандидатов (с дедупликацией по seen) |
| `invite_candidate()` | Приглашение кандидата |
| `get_messages()` | Получение сообщений |
| `_ensure_token()` | OAuth2 token refresh |

## Token Management

Токены хранятся в `secrets/rabota_tokens.json`. Автоматический refresh при expiry.

## Связанное

- [[материалы/документы/TrafficHub-obsidian/01-Architecture/DataFlow|Data Flow]]
- [[материалы/документы/TrafficHub-obsidian/05-Configuration/Config|Конфигурация]]
