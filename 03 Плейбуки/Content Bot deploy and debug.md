# Content Bot deploy and debug

## Когда использовать
Использовать при изменениях standalone Telegram `content-bot` на сервере.

## Проверить состояние
На сервере:

```bash
cd /root/TrafficHub
docker ps --format '{{.Names}} {{.Status}}' | grep standalone_content_bot
docker logs --tail 100 traffichub_standalone_content_bot
```

## Проверить код
```bash
cd /root/TrafficHub
python3 -m py_compile standalone_content_bot/app.py
```

Внутри контейнера:

```bash
docker exec -i traffichub_standalone_content_bot python - <<'PY'
import app
print(sorted(app.SETTINGS.admin_ids))
print(len(app.router.message.handlers), len(app.router.callback_query.handlers))
PY
```

## Проверить БД
```bash
docker exec traffichub_standalone_content_bot python -c "import sqlite3; c=sqlite3.connect('/data/bot.sqlite3'); cur=c.cursor(); [print(t, cur.execute('select count(*) from '+t).fetchone()[0]) for t in ['users','generations','events','admin_actions','access_rules','posts']]; c.close()"
```

## Пересобрать только content-bot
```bash
cd /root/TrafficHub
docker compose up -d --build standalone_content_bot
```

## Проверить руками в Telegram
- `/start`
- `/post`
- `/vacancy`
- `/history`
- `/profile`
- `/admin`

## Важные env
- `BOT_TOKEN` — Telegram bot token.
- `OPENROUTER_API_KEY` — AI provider key.
- `OPENROUTER_MODEL` — модель.
- `TARGET_CHAT_ID` — канал публикации.
- `ADMIN_PANEL_URL` — ссылка на AccountManager/web-panel.
- `DATABASE_PATH` — обычно `/data/bot.sqlite3`.
- `ADMIN_IDS` или `CONTENT_BOT_ADMIN_IDS` — Telegram ID администраторов.
- `ACCOUNT_MANAGER_INTERNAL_URL` — внутренний URL `Account Manager` для Telethon-источников, обычно `http://account_manager:8000`.
- `CONTENT_BOT_SHARED_KEY` — shared key между `standalone_content_bot` и `Account Manager` для internal `/api/telegram/internal/*`.

## Проверка Telethon-источников

Если `content_bot` должен брать посты из каналов через `📥 Источники`, проверять нужно не только сам bot, но и `Account Manager`:

```bash
cd /root/TrafficHub
KEY=$(awk -F= '/^CONTENT_BOT_SHARED_KEY=/{print $2}' .env)
curl -H "X-Content-Bot-Key: $KEY" http://127.0.0.1:8124/api/telegram/internal/accounts
curl -H "X-Content-Bot-Key: $KEY" "http://127.0.0.1:8124/api/telegram/internal/accounts/-1/channels?limit=5"
```

Если аккаунт legacy `tdata`, `id` в internal API будет отрицательным.

Для `tdata`-аккаунтов live runtime на `2026-06-28` подтверждён через `opentele2`, а не через старый `opentele`.

## Типовые проблемы
- Нет доступа к `/admin`: проверить `ADMIN_IDS` в `standalone_content_bot/.env`.
- История пустая после миграции: проверить таблицу `generations`, а не legacy `posts`.
- Бот не отвечает: проверить polling conflict в логах и наличие второго процесса с тем же `BOT_TOKEN`.
- Ошибка AI: проверить `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, сетевой доступ до `https://openrouter.ai`.
- `📥 Источники` пустые: проверить `/api/telegram/internal/accounts` и наличие server-side Telethon-сессии в `Account Manager`.
- Legacy `tdata` не открывается: проверить, что `session_path` указывает на server path вроде `/app/data/tdata_uploads/.../tdata`, а не на локальный `C:\...`.
- Каналы не читаются при валидном `tdata`: сначала проверить `proxy_id` у TG-аккаунта; недоступный proxy ломает Telethon source-read.
