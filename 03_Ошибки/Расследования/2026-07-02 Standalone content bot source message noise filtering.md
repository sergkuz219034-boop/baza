# 2026-07-02 Standalone content bot source message noise filtering

## Симптом

- При генерации из `Telethon`-источников в preview и LLM-context могли попадать не контентные сообщения:
  - flood/slowmode предупреждения;
  - anti-spam/captcha notices;
  - системные удаления сообщений;
  - требования подписаться на связанный канал.

## Зона системы

- live repo: `/root/TrafficHub`
- service: `standalone_content_bot`
- code: `/root/TrafficHub/standalone_content_bot/app.py`

## Гипотеза

- проблема не в `Account Manager` API и не в `Telethon` как transport-слое;
- шум попадает в генерацию, потому что `list_source_messages()` до этого брала первые `N` сообщений почти без нормализации и content/noise-классификации.

## Проверка

- Проверен live `app.py`:
  - до фикса `list_source_messages()` возвращала первые сообщения источника только со `strip()`;
  - фильтрации zero-width символов, flood-notices и moderation text не было.
- В live добавлены:
  - `SOURCE_NOISE_PATTERNS`;
  - `normalize_source_message_text()`;
  - `is_source_noise_message()`;
  - `sanitize_source_messages()`;
  - fetch с запасом (`safe_limit * 2`, capped at `10`) перед окончательной очисткой.
- Live compile-check:
  - `python -m py_compile standalone_content_bot/app.py` -> OK.
- Runtime smoke внутри `traffichub_standalone_content_bot`:
  - `list_source_channels(-1)` -> `18` joined dialogs;
  - выбран реальный source `ФРИЛАНС БАРАХОЛКА - работа на удаленке` (`dialog_id=-1001626008146`, `source_type=chat`);
  - `list_source_messages(-1, -1001626008146, limit=5)` вернул `5` нормальных сообщений;
  - в выдаче отсутствовали flood/anti-spam/moderation notices;
  - контейнер после rebuild healthy.

## Наблюдение

- Root issue был на стороне bot runtime sanitation, а не на стороне Telethon.
- Для noisy чатов нельзя брать первые `N` сообщений как есть: сначала нужен oversampling, потом чистка и dedupe.

## Вывод

- `content bot` теперь подаёт в preview и в source-based generation более чистый контекст.
- `TGStat/Telemetr` в этот фикс не входят; источник для этого сценария остаётся только `Telethon` через `Account Manager`.

## Следующий шаг

- Если всплывут новые шумовые паттерны, расширять `SOURCE_NOISE_PATTERNS` по live-наблюдениям.
- Если понадобится более точная фильтрация, выносить heuristics в отдельный source-sanitizer слой вместо роста `app.py`.
