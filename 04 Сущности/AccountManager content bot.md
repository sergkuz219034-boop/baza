# AccountManager content bot

## Назначение

Content bot в AccountManager управляет сбором/обработкой контента, целями публикации и задачами публикации в Telegram-каналы.

## Подтверждённые файлы

- `/root/TrafficHub/AccountManager/services/content_bot_service.py` — канонический сервис bot/runtime логики.
- `/root/TrafficHub/AccountManager/api/routers/content.py` — API для sources, targets, queued items, posting tasks и settings.
- `/root/TrafficHub/AccountManager/scheduler.py` — periodic jobs, включая polling Telegram updates.
- `/root/TrafficHub/AccountManager/dashboard/app.js` — dashboard controls для targets/tasks.
- `/root/TrafficHub/AccountManager/api/routers/telegram.py` — внутренний Telethon API для списка Telegram-аккаунтов, joined channels и чтения последних сообщений.
- `/root/TrafficHub/AccountManager/services/content_parser.py` — bridge `tdata -> Telethon client` для legacy Telegram accounts из `accounts.platform='tg'`.

## Runtime

Контейнер: `traffichub_account_manager`.

Content bot polling работает через scheduler job `content-bot-updates`.

После исправления 2026-06-20:

- interval: 10 секунд;
- `max_instances=1`;
- `coalesce=True`;
- Telegram `409 Conflict` считается single-poller конфликтом, а не аварией процесса;
- `httpx` INFO-логирование отключено, чтобы bot token не попадал в логи.

## Telethon contour

Подтверждённые Telegram-контуры в `Account Manager`:

- `telegram_accounts`
  - отдельные записи с `StringSession`;
  - используются `services.telethon_service.py`.
- `accounts.platform='tg'`
  - legacy Telegram/AyuGram profiles с `session_path` на `tdata`;
  - используются через `services.content_parser.py`.

Для internal API `content_bot` использует оба контура:

- positive `id` в `/api/telegram/internal/accounts` — записи из `telegram_accounts`;
- negative `id` — legacy `accounts.platform='tg'`.

На `2026-06-28` для live `tdata` подтверждён рабочий backend `opentele2`. Старый `opentele` на текущих `tdata` падал с `No account has been loaded`.

На `2026-07-09` подтверждён ещё один runtime-инвариант для legacy `tdata` контура:

- один `accounts.platform='tg'` аккаунт должен использовать один стабильный Telethon session file `legacy_account_{id}.session`;
- параллельный доступ к одному legacy account сериализуется в `services/content_parser.py`;
- старые временные `legacy_account_{id}_{uuid}.session` больше не должны генерироваться;
- `AuthKeyDuplicatedError` означает уже инвалидированный Telegram auth key, а не временный сетевой сбой. Для такого аккаунта нужен fresh `tdata` reimport.

## Ограничения

- Telegram `getUpdates` допускает только одного активного poller для bot token. Если другой процесс или webhook уже владеет обновлениями, Telegram возвращает `409 Conflict`.
- Legacy `tdata` аккаунт не становится рабочим только от факта сохранённого `session_path`: путь должен указывать на server-side `tdata`, доступный контейнеру.
- Недоступный proxy на TG-аккаунте ломает чтение каналов/сообщений даже при валидном `tdata`.

## Почему так

Scheduler не должен создавать параллельные poller instances: это повышает шанс Telegram conflict и засоряет логи. Поэтому polling ограничен одним экземпляром и более редким интервалом.

Отдельный internal Telethon API нужен, чтобы `standalone_content_bot` читал источники каналов из уже подключённого `Account Manager`, а не держал вторую Telethon-авторизацию.

## Проверка

- `docker logs --since 30s traffichub_account_manager`
- `docker exec traffichub_account_manager grep -n content-bot-updates /app/scheduler.py`
- `docker exec traffichub_account_manager grep -n BotPollingConflict /app/services/content_bot_service.py`
- `curl -H "X-Content-Bot-Key: ..." http://127.0.0.1:8124/api/telegram/internal/accounts`
- `curl -H "X-Content-Bot-Key: ..." "http://127.0.0.1:8124/api/telegram/internal/accounts/-1/channels?limit=5"`

## Связанные заметки

- [[2026-06-20 AccountManager content bot unfinished changes]]
- [[AccountManager Telegram polling conflict]]
- [[2026-06-28 AccountManager tdata Telethon live contour]]
- [[2026-07-09 AccountManager Telethon session invalidated by multi-IP reuse]]
