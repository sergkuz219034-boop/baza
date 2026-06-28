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
- admin UI может скрывать реальную причину отказа backend, если frontend не показывает `detail` из API.

## Пароли license accounts

Подтверждено расследованием [[2026-06-29 admin password update failed]] на live-сервере `/root/TrafficHub`.

- Валидация нового пароля находится в `utils/license.py::_validate_new_password`.
- Новый пароль должен быть не короче 4 символов.
- Служебные placeholders и маски (`пароль установлен`, `не задан`, `********` и т.п.) запрещены, чтобы admin UI не мог случайно сохранить текст из placeholder вместо реального пароля.
- Admin UI сохраняет пароль через `PATCH /api/settings/license-accounts/{login}` и должен показывать backend `detail`, иначе оператор видит только общий сбой.

## Где фигурировало

- [[2026-06-29 admin password update failed]]
