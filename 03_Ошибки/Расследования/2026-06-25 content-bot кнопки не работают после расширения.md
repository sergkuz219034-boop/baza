# 2026-06-25 content-bot кнопки не работают после расширения

## Симптом
После расширения `content-bot` часть кнопок не работала. В логах контейнера были ошибки:

```text
sqlite3.OperationalError: table user_state has no column named payload
```

Падали сценарии `/post`, `/vacancy` и ручной пост.

## Зона системы
- Контейнер: `traffichub_standalone_content_bot`
- Код: `/root/TrafficHub/standalone_content_bot/app.py`
- Runtime DB: `/data/bot.sqlite3`
- Таблицы: `user_state`, `drafts`

## Гипотеза
Код ожидал новую схему SQLite, но live-БД уже существовала со старой структурой. `CREATE TABLE IF NOT EXISTS` не меняет существующие таблицы, поэтому новые колонки не появились.

Дополнительный фактор: у пользователей в Telegram могла остаться старая persistent-клавиатура с прежними текстами кнопок.

## Проверка
Проверено на сервере:

```bash
docker logs --tail 200 traffichub_standalone_content_bot
```

Подтверждён root cause: `user_state` не имела `payload`, `drafts` не имела `input_json`.

После фикса:

```text
columns_user_state ['user_id', 'mode', 'topic', 'updated_at', 'payload']
columns_drafts ['user_id', 'draft_type', 'topic', 'text', 'created_at', 'input_json']
```

## Наблюдение
Для SQLite в standalone-сервисах нельзя полагаться только на `CREATE TABLE IF NOT EXISTS`. Любое изменение схемы существующей таблицы требует явной idempotent migration через `PRAGMA table_info` + `ALTER TABLE ADD COLUMN`.

## Вывод
Исправлено:
- добавлен helper `_ensure_column()`;
- `init_db()` теперь дообновляет старые таблицы;
- принудительно прогнана миграция live-БД через `app.init_db()`;
- добавлены обработчики старых кнопок Telegram:
  - `🤖 Сгенерировать пост`;
  - `📝 Создать пост`;
  - `🗂 Мои посты`;
  - `⚙️ Настройки`;
  - `👑 Админ-панель`.

## Следующий шаг
При следующих изменениях `content-bot` проверять не только новую пустую БД, но и существующую live-БД с legacy-таблицами.
