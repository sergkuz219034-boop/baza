# 2026-07-02 Standalone content bot source paging

## Симптом

- После добавления фильтров и preview вкладка `Источники` всё ещё упиралась в верхнюю часть joined dialogs:
  - bot UI показывал только первую часть списка;
  - внутренний `Account Manager` endpoint обрезал список `channels` лимитом `30`;
  - при больших Telethon-аккаунтах пользователь не мог дойти до хвостовой части `чатов/каналов`.

## Зона системы

- live repo: `/root/TrafficHub`
- service: `account_manager`
- service: `standalone_content_bot`
- code:
  - `/root/TrafficHub/AccountManager/api/routers/telegram.py`
  - `/root/TrafficHub/standalone_content_bot/app.py`

## Гипотеза

- для нормального UX нужен не только bot-side paging;
- сначала надо перестать обрезать joined dialogs слишком низким limit на internal API.

## Проверка

- Проверен live `AccountManager/api/routers/telegram.py`:
  - до фикса `internal/accounts/{account_id}/channels` ограничивал `safe_limit` значением `30`.
- В live внесён фикс:
  - internal API limit поднят до `100`;
  - `content bot` запрашивает `/internal/accounts/{account_id}/channels?limit=100`;
  - bot-side paging добавлен в `sources_account` state с сохранением `filter` и `page`.
- Runtime smoke внутри `traffichub_standalone_content_bot`:
  - у аккаунта `Виктория` (`id=-1`) получено `18` joined dialogs;
  - после фильтра `chat` осталось `14` dialogs;
  - page split подтвердился как `8 + 6`;
  - `render_source_channels(-1, 'chat', 1)` вернул текст `Страница: 2 из 2`.

## Наблюдение

- root issue был двухслойным:
  - API layer обрезал данные слишком рано;
  - bot UX не умел листать filtered dialogs.
- После фикса navigation работает так:
  - `⬅️ Назад список`
  - `➡️ Ещё источники`
  - фильтр `все / чаты / каналы` не теряется между страницами;
  - `↩️ Назад` из preview возвращает к тому же account/filter/page.

## Вывод

- `content bot` теперь не ограничен первой страницей joined dialogs.
- Для Telethon-аккаунтов со средним объёмом чатов и каналов источник можно выбрать полностью, без ручного уменьшения списка.

## Следующий шаг

- Если у аккаунтов появятся `100+` joined content dialogs:
  - поднимать internal limit ещё выше или переходить на cursor/offset схему;
  - при необходимости отдельно page-ить не только bot UI, но и сам internal API.
