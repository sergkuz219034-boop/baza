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

## Типовые проблемы
- Нет доступа к `/admin`: проверить `ADMIN_IDS` в `standalone_content_bot/.env`.
- История пустая после миграции: проверить таблицу `generations`, а не legacy `posts`.
- Бот не отвечает: проверить polling conflict в логах и наличие второго процесса с тем же `BOT_TOKEN`.
- Ошибка AI: проверить `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, сетевой доступ до `https://openrouter.ai`.
