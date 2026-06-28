# 2026-06-28 AccountManager tdata Telethon live contour

## Симптом

- `standalone_content_bot` не мог брать источники из Telegram-каналов через Telethon.
- В `Account Manager` карточка Telegram-аккаунта показывала локальный Windows-путь вида `C:\Users\Арт\Desktop\Telegram\...`, но live-сервер не получал из этого рабочую Telethon-сессию.

## Зона системы

- live repo: `/root/TrafficHub`
- `AccountManager/api/routers/telegram.py`
- `AccountManager/services/content_parser.py`
- `AccountManager/services/telethon_service.py`
- `standalone_content_bot/app.py`
- PostgreSQL tables:
  - `accounts`
  - `telegram_accounts`

## Гипотеза

- контур `tdata -> Telethon` в live был недоделан;
- `AccountManager` хранил `accounts.platform='tg'` с `session_path`, но не умел строить из него live Telethon client;
- старый путь через `opentele` мог быть несовместим с текущими `tdata`.

## Проверка

- В live PostgreSQL:
  - `telegram_accounts = 0`
  - `accounts where platform='tg' = 1`
- У существующего `accounts.id=1` был `session_path = C:\Users\Арт\Desktop\Telegram\Яна`, то есть путь не из server filesystem.
- В коде `AccountManager/api/routers/accounts.py` уже были вызовы `services.content_parser.get_client`, но `AccountManager/services/content_parser.py` содержал только пустой stub.
- В `AccountManager/data/tdata_uploads/` найдены server-side копии `tdata`.
- Runtime-проверка показала:
  - старый `opentele` падает на текущих `tdata` с `OpenTeleException: No account has been loaded`;
  - `opentele2` успешно открывает `tdata` и через `TDesktop(...).ToTelethon(...)` отдаёт Telethon client.
- Для `tdata` по пути `/app/data/tdata_uploads/_jcpc2G4JUk/Виктория/tdata` live runtime вернул пользователя:
  - `id=8127966108`
  - `username=JobVictory`
  - `first_name=Виктория`
- После отвязки мёртвого proxy от `accounts.id=1` internal API начал успешно отдавать:
  - joined channels: `GET /api/telegram/internal/accounts/-1/channels`
  - последние посты канала: `GET /api/telegram/internal/accounts/-1/messages`

## Наблюдение

- `telegram_accounts` и `accounts.platform='tg'` — это два разных контура Telegram в `Account Manager`.
- Для `content_bot` критичен именно server-side Telethon runtime, а не просто сохранённый путь в UI.
- На текущих `tdata` нужно использовать `opentele2`, а не старый `opentele`.
- Наличие proxy на TG-аккаунте может ломать чтение каналов даже при валидном `tdata`, если proxy недоступен.
- Для legacy `tdata` аккаунтов internal API сейчас использует отрицательные `id`:
  - `-1` означает `accounts.id=1`

## Вывод

- live Telethon contour для `tdata` восстановлен через `opentele2`;
- `standalone_content_bot` может использовать `Account Manager` как внутренний источник каналов и постов;
- прежняя проблема была не в `content_bot`, а в отсутствии рабочего server-side bridge из `accounts.session_path` в Telethon client.

## Следующий шаг

- При добавлении нового Telegram `tdata` в `Account Manager` сохранять именно server-side путь из `data/tdata_uploads/...`, а не локальный Windows path.
- Если чтение каналов снова ломается, сначала проверять:
  - `proxy_id` у Telegram-аккаунта;
  - `GET /api/telegram/internal/accounts`;
  - `GET /api/telegram/internal/accounts/-N/channels`;
  - наличие `opentele2` в runtime `traffichub_account_manager`.
