# Infrastructure

Теги: #архитектура

## Сервисы

- `autolead_bot`
- `license_auth`
- `account_manager`
- `caddy`

## Домены

- основной public domain для dashboard/runtime
- отдельный domain для `license_auth`
- отдельный domain для `AccountManager`
- отдельный domain для AI redirect perimeter

## Хранилища

- `./data`
- `./secrets`
- `./AccountManager/data`
- Caddy volumes для config/data

## Почему инфраструктура такая

- сервисы разнесены по функциям и auth-perimeter;
- публичный доступ централизован через Caddy;
- runtime и control данные сохраняются в volume-mounted SQLite и secrets directory.

## Смежные страницы

- [[Deployment]]
- [[Monitoring]]
