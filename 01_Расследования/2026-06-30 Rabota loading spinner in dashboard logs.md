# 2026-06-30 Rabota loading spinner in dashboard logs

## Симптом

В dashboard terminal вместо стабильной бизнес-строки появился transient progress вида `⠋ Загрузка откликов: 100...`.

## Зона системы

- `modules/rabota_api.py`
- `utils/runtime_logging.py`
- `tests/test_runtime_logging.py`
- live containers: `traffichub_app`, `traffichub_worker`

## Гипотеза

Это не новый job-spinner dashboard, а legacy console-spinner Rabota.ru, который попадает в web logs как обычная строка в non-TTY окружении.

## Проверка

- `modules/rabota_api.py::_spin()` печатал `Загрузка откликов` / `Загрузка автоподбора`.
- В TTY это был carriage-return spinner, но в non-TTY branch код печатал новую строку каждые 10 кадров.
- `utils/runtime_logging.py::is_ui_relevant_log()` дополнительно пропускал строки `⠋ Загрузка ...` и `✓ Загрузка ...` в dashboard UI.
- Скрин пользователя совпал с форматом `_spin("Загрузка откликов", len(all_items), ...)`.

## Наблюдение

После фикса основного `Полный цикл выполняется` этот старый Rabota progress стал визуально заметен как отдельная строка. Это другой источник того же класса UI-шума: transient terminal animation не должна превращаться в persistent dashboard log.

## Вывод

Канон: `Загрузка откликов` и `Загрузка автоподбора` являются transient progress, а не пользовательскими log events. В dashboard должны оставаться финальные смысловые строки вроде `Уникальных откликов:` и `Автоподбор итого:`.

Фикс product commit `cf12e5062`:

- `modules/rabota_api.py::_spin()` пишет spinner только в интерактивный TTY;
- `_spin_done()` больше не пишет финальную transient строку в non-TTY;
- `utils/runtime_logging.py` отбрасывает legacy строки `⠋/⠙/.../✓ Загрузка откликов|автоподбора`;
- `tests/test_runtime_logging.py` закрепляет этот guardrail.

Live deploy:

- GitHub Actions `CI` и `Build and Push Docker Image` зелёные;
- пересозданы `traffichub_app` и `traffichub_worker`;
- `/api/health` вернул `status=ok`;
- внутри обоих контейнеров `/app` подтверждены новый Rabota spinner code и runtime logging regex.

## Следующий шаг

Если похожие transient строки снова появятся, искать source-level console spinner по `print()` / `sys.stdout.write()` и добавлять двойной guardrail: не печатать в non-TTY и отбрасывать в `is_ui_relevant_log()`.
