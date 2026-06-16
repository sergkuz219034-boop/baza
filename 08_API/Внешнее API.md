# Внешнее API

## Подтверждённый минимум

- license auth / license server — отдельный внешний auth-контур;
- Account Manager имеет собственный app boundary;
- точный каталог внешних public endpoints нужно подтверждать отдельно.

## Отдельно про bridge

- `GET /api/account-manager/token` доступен аутентифицированному пользователю;
- endpoint выдаёт HS256 JWT для перехода в Account Manager;
- роль окончательно проверяется уже на стороне Account Manager.

## Ограничение

Если в старых заметках websocket или access-path описан как чистый Basic-auth flow, это считать устаревшим описанием.

## Дополнительные источники

- [[raw/docs/TrafficHub-obsidian/04 Сущности/Auth и Access|Auth и Access]]
- [[raw/docs/TrafficHub-obsidian/03-API/Auth|Legacy API auth]]
