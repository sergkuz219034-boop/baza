---
title: 2026-06-30 AccountManager telegram dialog split for chats vs content
---

# 2026-06-30 AccountManager telegram dialog split for chats vs content

## Симптом

- Пользователь запросил разнести Telegram-диалоги по двум сценариям:
  - кнопка `Переписки` должна показывать только личные диалоги с людьми;
  - `Content Bot` должен работать только с чатами и каналами, без личных переписок.

## Зона системы

- `AccountManager` Telegram dialog filtering.
- Файлы:
  - `AccountManager/api/routers/accounts.py`
  - `AccountManager/services/content_parser.py`
  - `AccountManager/services/telethon_service.py`
  - `AccountManager/utils/telegram_dialog_filters.py`

## Гипотеза

- Сейчас один и тот же общий список Telethon dialogs используется с разной бизнес-семантикой, из-за чего личные диалоги и контентные сущности не разделены явно.

## Проверка

- `POST /api/accounts/{id}/telethon-dialogs` ранее возвращал все dialogs без фильтра по типу.
- `AccountManager/services/content_parser.py:list_channels()` и `AccountManager/services/telethon_service.py:list_account_channels()` фильтровали только `is_channel`, то есть:
  - пропускали каналы;
  - отбрасывали группы;
  - не имели общего канона с `telethon-dialogs`.
- Введён общий helper `AccountManager/utils/telegram_dialog_filters.py` с двумя правилами:
  - `is_personal_dialog()` → только `is_user`, без `is_group/is_channel`;
  - `is_content_dialog()` → только `is_group/is_channel`, без `is_user`.
- Прогнаны regression tests `tests/test_account_manager_telegram_filters.py` и `tests/test_account_manager_content.py`.

## Наблюдение

- После фикса live probe для `telethon-dialogs` вернул только `telethon_dialog_kinds = ["user"]`.
- Для content-discovery на проверенном legacy `tdata` аккаунте список оказался пустым, то есть личные переписки туда больше не протекают; joined групп/каналов у этого аккаунта в момент проверки не было.

## Вывод

- Source of truth теперь разделён по бизнес-назначению:
  - `Переписки` = только люди;
  - `Content Bot` = только группы и каналы.
- Логика вынесена в общий helper, чтобы backend AccountManager и content-runtime не расходились по фильтрации.

## Следующий шаг

- Если понадобится UI-автоподбор Telegram-источников/целей в `Content Bot`, использовать только content-filtered список из `groups/channels`, а не общий список dialogs.
