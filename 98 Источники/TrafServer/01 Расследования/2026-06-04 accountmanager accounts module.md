# 2026-06-04 accountmanager accounts module

Теги: #debug #архитектура

## Симптом

Пользователь попросил доделать Account Manager, а в workspace из его кода был доступен только `AccountManager/api/main.py`.

## Зона

- `remote_server_snapshot/AccountManager`
- `TZ_AccountManager_Accounts.docx`

## Гипотеза

Сервис не просто недоделан, а в snapshot отсутствует почти весь backend-каркас для модулей Telegram, Google и VK/Max.

## Проверка

- Извлечён текст ТЗ из `TZ_AccountManager_Accounts.docx`.
- Прочитан `remote_server_snapshot/AccountManager/api/main.py`.
- Проверено содержимое `remote_server_snapshot/AccountManager`.

## Наблюдение

- `main.py` ожидает пакеты `database`, `api.routers`, `services.content_parser`, но их исходников в snapshot не было.
- ТЗ требует новые таблицы и endpoint-группы `/api/telegram/*`, `/api/google/*`, `/api/social/*`.
- Без добора этих модулей Account Manager даже не может подняться как самодостаточный snapshot.

## Вывод

Для meaningful completion нужен backend scaffold: модели, роутеры, сервисы, базовая dashboard-страница и интеграция новых роутеров в `main.py`.

## Следующий шаг

- Проверить импорт, smoke flow и frontend/extension assets.
- Зафиксировать ограничения live OAuth/Telethon flow в wiki.
