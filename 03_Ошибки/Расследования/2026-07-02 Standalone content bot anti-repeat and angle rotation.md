# 2026-07-02 Standalone content bot anti-repeat and angle rotation

## Симптом

- Пользователь просит проверить, насколько `content bot` публикует случайные/уникализированные посты и не повторяет старые формулировки "как раньше".

## Зона системы

- live repo: `/root/TrafficHub`
- service: `standalone_content_bot`
- runtime DB: `/root/TrafficHub/standalone_content_bot/data/bot.sqlite3`
- code: `/root/TrafficHub/standalone_content_bot/app.py`

## Гипотеза

- в live уже есть частичная вариативность через `recent_channel_posts()` и список `angles`, но нет жёсткой anti-repeat валидации;
- из-за этого посты не обязаны быть буквальными дублями, но могут повторяться по заголовку, открывающему абзацу и общей структуре.

## Проверка

- Проверен live-код:
  - `call_llm(... temperature=0.75)`
  - `recent_channel_posts(target_chat_id, limit=6)`
  - фиксированный список углов для автопостинга
  - `is_generic_job_post()` с набором generic-фраз
- Проверены последние опубликованные post-generation в SQLite.
- До фикса были видны серийные похожие посты по `@cadrypro_official` с близкой общей рамкой "новые возможности / работа мечты / открой горизонты".
- После фикса в live добавлены:
  - `POST_ANGLE_POOL`
  - `detect_repeat_risk()`
  - rotation углов по каналу
  - regeneration loop перед publish
  - deterministic fallback с несколькими вариантами шаблона
- Runtime-проверка внутри контейнера:
  - два подряд вызова `generate_unique_post_variant()` для одного канала вернули разные углы;
  - `detect_repeat_risk()` для обоих результатов вернул `(False, "ok")`.

## Наблюдение

- Ранее уникализация была мягкой эвристикой на уровне промпта и recent digest.
- Теперь anti-repeat стал runtime-механикой, а не только пожеланием к LLM:
  - сравниваются заголовок, opening fragment и нормализованный body;
  - при превышении порога вариант отклоняется и модель генерирует новый;
  - в prompt memory подмешиваются и отклонённые варианты.
- Ручная генерация поста тоже использует anti-repeat, если у пользователя есть активный канал.

## Вывод

- На live `content bot` больше не полагается только на `temperature` и удачу модели.
- Уникализация стала существенно сильнее, но пока это всё ещё lightweight-heuristics, а не semantic embedding memory.
- Слабое место, которое осталось:
  - нет vector/embedding similarity;
  - нет хранения структурных метаданных поста как отдельной памяти канала;
  - нет канального blacklist по hook-шаблонам вне текущих regexp/ratio checks.

## Следующий шаг

- Если понадобится усиление до "почти без повторов":
  - хранить для канала memory-card постов (`title/opening/angle/cta`);
  - добавить semantic similarity поверх lexical checks;
  - запретить повтор angle в коротком окне последних N публикаций.
