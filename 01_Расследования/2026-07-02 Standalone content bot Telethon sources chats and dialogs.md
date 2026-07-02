# 2026-07-02 Standalone content bot Telethon sources chats and dialogs

## Симптом

- Пользователь уточнил, что для `content bot` нужны не внешние `TGStat/Telemetr`, а собственные `Telethon`-источники из `Account Manager`.
- Ранее в UX и части кода всё это называлось `каналами`, хотя runtime уже работал по joined `dialogs`.

## Зона системы

- live repo: `/root/TrafficHub`
- service: `standalone_content_bot`
- service: `account_manager`
- code:
  - `/root/TrafficHub/standalone_content_bot/app.py`
  - `/root/TrafficHub/AccountManager/services/telethon_service.py`
  - `/root/TrafficHub/AccountManager/services/content_parser.py`

## Гипотеза

- `content bot` уже получает не только каналы, а `is_group/is_channel` dialogs из `Telethon`, но:
  - API не отдаёт тип источника;
  - UX продолжает называть всё `каналами`;
  - пользователь не видит разницу между `чатом`, `каналом` и `каналом с обсуждением`.

## Проверка

- Проверен фильтр `AccountManager/utils/telegram_dialog_filters.py`:
  - `is_content_dialog(dialog)` возвращает `True` для `is_group` или `is_channel`;
  - значит контентный Telethon-path уже не ограничен только каналами.
- Проверены live-сервисы:
  - `/root/TrafficHub/AccountManager/services/telethon_service.py`
  - `/root/TrafficHub/AccountManager/services/content_parser.py`
  - ранее они сериализовали joined dialogs как однотипные `channels`.
- В live внесён фикс:
  - добавлены `source_type`, `source_label`, `has_comments`;
  - bot UX переведён на термин `источники Telethon`, а не только `каналы`.
- Runtime smoke внутри `traffichub_standalone_content_bot`:
  - `list_source_accounts()` вернул `6` активных внутренних Telegram-аккаунтов;
  - по первым аккаунтам подтверждены смешанные типы joined dialogs:
    - `Анна`: `17 dialogs` = `8 чатов`, `9 каналов`;
    - `Виктория`: `18 dialogs` = `14 чатов`, `4 канала`;
    - `Карина`: `6 dialogs` = `1 чат`, `5 каналов`.
- Отдельно проверен флаг `has_comments` по первым `limit=20` joined dialogs доступных аккаунтов:
  - в текущем live-срезе таких dialogs не найдено.

## Наблюдение

- Root issue был не в отсутствии Telethon-chat support, а в неверной продуктовой surface-модели:
  - runtime уже читал `groups/channels`;
  - API и bot UX продолжали говорить только про `каналы`.
- После фикса:
  - `content bot` выбирает источник как `чат`, `канал` или `канал с комментариями`;
  - `Telethon`-источник используется как единый класс `dialogs`;
  - генерация черновика теперь текстово описывает именно `источник`, а не обязательно `канал`.

## Вывод

- Для `content bot` внешний discovery через `TGStat/Telemetr` не нужен в этом контуре.
- Нужный и уже рабочий канон здесь — `Telethon dialogs` из `Account Manager`.
- Live подтверждает, что бот может брать основу не только из каналов, но и из joined чатов.

## Следующий шаг

- Если нужна более сильная surface:
  - вынести `чаты` и `каналы` в отдельные фильтры внутри `Источники`;
  - добавить preview последних сообщений до генерации;
  - при появлении live dialogs с `linked_chat_id` отдельно подсветить `каналы с комментариями` как first-class источник.
