# 2026-07-02 Standalone content bot source modes and depth

## Симптом

- После добавления preview и paging генерация по `Telethon`-источнику всё ещё оставалась слишком жёсткой:
  - один фиксированный режим генерации;
  - одна и та же глубина контекста;
  - пользователь не мог выбрать между более свободным новым постом и более близким рерайтом по мотивам источника.

## Зона системы

- live repo: `/root/TrafficHub`
- service: `standalone_content_bot`
- code: `/root/TrafficHub/standalone_content_bot/app.py`

## Гипотеза

- нужные данные уже есть в `Telethon`-источнике;
- проблема находится в отсутствии управляемого generation-mode слоя в `sources_preview`.

## Проверка

- Проверен live `app.py`:
  - до фикса `generate_source_post()` и `source_post_user_prompt()` работали по одному и тому же сценарию;
  - `list_source_messages()` всегда брала фиксированную глубину контекста.
- В live добавлены:
  - режимы `🧠 Новый пост` и `♻️ Рерайт`;
  - переключатели глубины контекста `3 / 5 / 8 сообщений`;
  - сохранение `source_mode` и `source_message_limit` в `sources_preview` state и в payload generation history.
- Runtime smoke внутри `traffichub_standalone_content_bot`:
  - `source_generation_mode_label('fresh') -> новый пост`;
  - `source_generation_mode_label('rewrite') -> рерайт`;
  - `detect_source_mode('♻️ Рерайт') -> rewrite`;
  - `detect_source_limit('8 сообщений') -> 8`;
  - preview-текст показывает выбранные `режим` и `глубину контекста`.
- Дополнительная live-проверка на реальном joined dialog:
  - `list_source_messages(-1, <real_dialog_id>, limit=8)` вернул `200 OK` и список сообщений;
  - значит новый `message_limit=8` не ломает internal API.

## Наблюдение

- Root issue был не в Telethon и не в AI provider, а в слишком узком UX control surface:
  - пользователю не хватало выбора сценария генерации;
  - bot runtime не позволял осознанно увеличить или уменьшить объём source-context.
- После фикса preview стал не только read-only, а управляющим экраном генерации.

## Вывод

- `content bot` теперь позволяет:
  - сделать более свободный `новый пост` по мотивам источника;
  - сделать более близкий `рерайт`;
  - варьировать глубину контекста без повторного выбора источника.

## Следующий шаг

- Если потребуется усиление:
  - добавлять отдельный режим `подборка/саммари`;
  - фильтровать шумные system-messages/moderation-warnings перед подачей в LLM;
  - сохранить user-default mode/depth для следующих генераций.
