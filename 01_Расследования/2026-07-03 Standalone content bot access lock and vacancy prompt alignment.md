# 2026-07-03 Standalone content bot access lock and vacancy prompt alignment

## Симптом

- `content bot` формально должен был быть доступен только двум Telegram `user_id`, но live runtime не имел отдельного allowlist enforcement.
- `users.role` в SQLite расходился с текущим `ADMIN_IDS`: один из действующих админов оставался в БД как `user`.
- Текст экрана `Автопостинг` утверждал, что новые посты публикуются сразу после генерации, хотя по коду ручные черновики публикуются только после явного подтверждения.
- Smoke на `generate_from_data('vacancy', {'topic': ...})` показал потерю темы и произвольную роль (`HR-архитектор`), потому что vacancy prompt брал только `role`.

## Зона системы

- live repo: `/root/TrafficHub`
- service: `standalone_content_bot`
- code: `/root/TrafficHub/standalone_content_bot/app.py`
- runtime DB: `/data/bot.sqlite3`

## Гипотеза

- доступ ограничивался только через `ADMIN_IDS` и ручные блокировки в БД, но не через общий allowlist-path;
- `track_user()` не синхронизировал `role` при повторных входах;
- UX-текст автопостинга устарел относительно фактической логики публикации;
- vacancy generation имела data-shape drift между `role` и `topic`.

## Проверка

- Проверен live `app.py` до фикса:
  - `Settings` не имел `allowed_user_ids`;
  - `track_user()` обновлял счётчики и `last_seen_at`, но не приводил `role/status` к текущей access-модели;
  - `admin_autopost_text()` писал, что посты публикуются сразу после генерации;
  - `vacancy_user_prompt()` использовал только `data.get("role")`.
- Проверена live DB `bot.sqlite3`:
  - в `users` был посторонний `user_id=8147779865` со статусом `active`;
  - `934602871` был в `role='user'`, хотя текущий runtime считает его админом;
  - active channels и schedule остались owner-scoped.
- В live добавлено:
  - `allowed_user_ids` в `Settings` с fallback на `ALLOWED_USER_IDS` или `ADMIN_IDS`;
  - helper `is_allowed_user()`;
  - `track_user()` теперь синхронизирует `role`, принудительно блокирует неразрешённые `user_id` и не считает их активными;
  - `require_active()` теперь отвечает нейтральным текстом `Доступ к боту ограничен`;
  - `admin_autopost_text()` приведён к реальному поведению: scheduler-only, без авто-публикации ручных черновиков;
  - `vacancy_user_prompt()` берёт `role` или fallback `topic`.
- Runtime smoke внутри `traffichub_standalone_content_bot` после rebuild:
  - `allowed_user_ids = {7512871059, 934602871}`;
  - `track_user(7512871059) -> True`;
  - `track_user(8147779865) -> False`;
  - `list_scheduled_channels()` вернул только активный канал `#26` пользователя `934602871`, а не весь owner pool;
  - `generate_from_data('vacancy', {'topic': 'оператор контакт-центра'})` вернул вакансию по теме, а не произвольную роль;
  - `generate_from_data('vacancy', {'role': 'оператор контакт-центра'})` тоже отработал корректно.
- Runtime DB backfill внутри контейнера:
  - оба разрешённых `user_id` переведены в `role='admin', status='active'`;
  - `8147779865` переведён в `status='blocked'`.

## Наблюдение

- Root issue был не в Telegram API и не в OpenRouter, а в двух локальных расхождениях:
  - access model существовала как договорённость, но не была жёстко зашита в runtime;
  - vacancy prompt depended on one payload shape, а часть runtime-paths передавала другой.

## Вывод

- Live `content bot` теперь реально закрыт allowlist-моделью, а не только админским UI.
- Админские роли в SQLite синхронизированы с текущей конфигурацией.
- Экран `Автопостинг` больше не вводит в заблуждение относительно ручных черновиков.
- Vacancy generation перестала терять тему, если во входных данных используется `topic`.

## Следующий шаг

- Если потребуется расширение доступа, менять `ALLOWED_USER_IDS`/`ADMIN_IDS` согласованно, а не только UI-ролями в БД.
- Если `standalone_content_bot` продолжит расти, выносить access/prompt policy из монолитного `app.py` в отдельные слои.
