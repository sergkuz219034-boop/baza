# License layer

Теги: #сущность

## Тип

Модуль

## Где находится

`remote_files/utils/license.py`

## Роль в системе

Обеспечивает validate_user, роли, кэш пользователей, sync auth/config в control store и legacy compatibility с Google Sheets.

## Входы

- `control.db`
- `secrets/*.json`
- env variables

## Выходы

- auth validation
- role resolution
- bootstrap/migration side effects

## Зависимости

- [[Control store]]
- [[Authentication]]

## Типовые сбои или риски

- высокая сложность;
- legacy compatibility code увеличивает шанс drift.
