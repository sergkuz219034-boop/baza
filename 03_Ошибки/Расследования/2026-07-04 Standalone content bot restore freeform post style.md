# 2026-07-04 Standalone content bot restore freeform post style

## Симптом

- На live `content bot` посты перестали выглядеть живыми и начали повторять один и тот же каркас.
- Реальные опубликованные посты в `generations` и канале сходились по одной схеме:
  - одинаковый hook;
  - одинаковые блоки вроде `кому подойдет / что проверить`;
  - визуально похожие CTA и повторяющаяся emoji-подача.

## Зона системы

- live repo: `/root/TrafficHub`
- service: `standalone_content_bot`
- code: `/root/TrafficHub/standalone_content_bot/app.py`
- runtime data: `/data/bot.sqlite3`

## Гипотеза

- проблема не в отсутствии anti-repeat как такового, а в том, что сам generation-core слишком жёстко задаёт одну и ту же форму текста;
- дополнительно повторяемость усиливают:
  - post-processing с принудительным emoji-flair;
  - deterministic fallback, который строит почти одинаковые шаблоны;
  - слишком узкий `post_user_prompt`.

## Проверка

- Проверена live-история `generations`:
  - последние опубликованные `post` были похожи по opening и композиции;
  - различия были косметическими, а не смысловыми.
- Сравнены live `app.py` и ранние рабочие версии:
  - ранний standalone contour имел более свободную модель генерации;
  - текущий live `post_user_prompt()` заставлял LLM почти всегда идти по одной схеме;
  - `prepare_post_text_for_publish()` дополнительно накидывал emoji после генерации;
  - при неудаче anti-repeat включался шаблонный `build_deterministic_job_post()`.
- После фикса выполнен live smoke внутри `traffichub_standalone_content_bot`:
  - несколько вызовов `generate_unique_post_variant('заработок', ...)` вернули разные opening hooks и разную композицию;
  - `generate_from_data('post', ...)` больше не тяготеет к одному шаблону `кому подойдет / что проверить`.

## Наблюдение

- Root issue был не в scheduler, не в каналах и не в Telethon-источниках.
- Повторяемость возникала из-за слишком жёсткого prompt-contract и пост-обработки, а не из-за отсутствия LLM-вариативности.

## Вывод

- В live возвращён более свободный ранний стиль генерации постов без отката новых функций:
  - каналы, active channel, owner-scoped autopost;
  - Telethon `/sources`, preview, paging, mode/depth;
  - history, drafts, кнопки, allowlist.
- Что изменено в generation-core:
  - `post_user_prompt()` снова стал свободным и не навязывает один и тот же каркас;
  - `prepare_post_text_for_publish()` больше не добавляет forced emoji-flair поверх ответа модели;
  - post-generation идёт с немного более высокой вариативностью;
  - перед deterministic fallback добавлен ещё один LLM rescue-pass.

## Следующий шаг

- Если посты снова начнут схлопываться в одну форму, следующая точка проверки — не channels/autopost, а prompt drift в `prompts` table и live samples в `generations`.
- Если понадобится усилить уникализацию дальше, лучше идти в сторону richer anti-repeat memory и angle families, а не обратно в жёсткие шаблоны.
