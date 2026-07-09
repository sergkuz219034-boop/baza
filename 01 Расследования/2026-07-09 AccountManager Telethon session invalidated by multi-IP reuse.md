---
title: 2026-07-09 AccountManager Telethon session invalidated by multi-IP reuse
---

# 2026-07-09 AccountManager Telethon session invalidated by multi-IP reuse

## Симптом

- В `AccountManager` у части текущих Telegram-аккаунтов tooltip/статус показывал:
  - `The authorization key (session file) was used under two different IP addresses simultaneously...`
- В UI это выглядело как обычная ошибка Telethon-подключения без явного действия для восстановления.

## Зона системы

- `AccountManager` Telethon bridge для legacy `accounts.platform='tg'`.
- Файлы:
  - `/root/TrafficHub/AccountManager/services/content_parser.py`
  - `/root/TrafficHub/AccountManager/api/routers/accounts.py`
  - `/root/TrafficHub/tests/test_account_manager_telethon_session_files.py`

## Гипотеза

- Общий кодовой путь на каждый Telethon-check/чтение переписок создавал новый `.session` файл из одного и того же `tdata`, из-за чего Telegram видел параллельное использование одного auth key с разных IP/session-contour и инвалидировал ключ.
- После инвалидирования конкретный `tdata` уже нельзя восстановить простым повторным check.

## Проверка

- В live `services/content_parser.py` до фикса `_session_file_for_account()` генерировал `legacy_account_{id}_{uuid}.session`, а cleanup удалял временный файл после работы клиента.
- В runtime-папке `/app/data/runtime/telethon_sessions` были десятки файлов вида:
  - `legacy_account_3_<uuid>.session`
  - `legacy_account_7_<uuid>.session`
- После server-side фикса:
  - для аккаунта `3` прямой вызов `get_client()` два раза подряд дал успешный результат на одном stable файле `legacy_account_3.session`;
  - для аккаунта `1` (`Виктория`) даже после удаления stable `.session` ошибка осталась той же: `AuthKeyDuplicatedError`.

## Наблюдение

- Root cause был системным, а не owner-specific: legacy Telethon bridge плодил новые session-файлы и не сериализовал доступ по аккаунту.
- После устранения root cause старые рабочие аккаунты продолжают авторизоваться стабильно.
- Если Telegram уже инвалидировал auth key, этот конкретный `tdata` не лечится кодом и требует свежей авторизованной `tdata`.

## Вывод

- В live/product repo закреплено новое правило:
  - один Telegram legacy account -> один стабильный Telethon session file `legacy_account_{id}.session`;
  - доступ к Telethon по аккаунту сериализуется через `asyncio.Lock`;
  - старые UUID-session артефакты удаляются;
  - при `AuthKeyDuplicatedError` UI/статус получает явное сообщение: нужен reimport новой `tdata`.
- Для текущего проблемного аккаунта `1` проблема уже не в коде, а в инвалидированном Telegram auth key.

## Следующий шаг

- Для аккаунтов со статусом `Telethon session invalidated by Telegram...` нужно переимпортировать профиль с новой валидной `tdata`.
- Если симптом повторится на новых аккаунтах после этого фикса, надо отдельно проверять внешний параллельный клиент/сервер, который использует тот же Telegram auth key вне `AccountManager`.
