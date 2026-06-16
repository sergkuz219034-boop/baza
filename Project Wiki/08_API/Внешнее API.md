# Внешнее API

## Подтверждённый минимум

- license auth / license server — отдельный внешний auth-контур;
- Account Manager имеет собственный app boundary;
- точный каталог внешних public endpoints нужно подтверждать отдельно.

## Отдельно про bridge

- `GET /api/account-manager/token` доступен аутентифицированному пользователю;
- endpoint выдаёт HS256 JWT для перехода в Account Manager;
- роль окончательно проверяется уже на стороне Account Manager.
