# Onecta BetaOnline и ложные ошибки Playwright

## Симптом

Dashboard показывал `tilda ФИО: поле имени не найдено` и блок `Task was destroyed` / `TargetClosedError`, хотя Onecta №2 успешно отправлялась.

## Зона системы

`modules/platforms/tilda.py`, `modules/vbiv_bot.py`.

## Гипотеза

Onecta №2 использует BetaOnline/Vue, не Tilda: поля называются `firstname` и `lastname`. Красные Playwright-строки — ложный async teardown после закрытого browser.

## Проверка

HTML-артефакт `debug_Onecta__2_ARTEM_20260803_111110.html` показал поля BetaOnline. После production rebuild выполнена одна реальная анкета Onecta №2 ARTEM.

## Наблюдение

Итоговый isolated runtime log: `sent=1`, `errors=0`; отсутствуют `tilda ФИО`, `Task was destroyed`, `Future exception was never retrieved`, `TargetClosedError`.

## Вывод

Для BetaOnline generic selector `input[name=name]` не логируется как ошибка. Ложный teardown-блок Playwright фильтруется точечно; реальные form/network ошибки не скрываются. Fallback сохранён в image, а не только через `docker cp`.

## Дополнительная проверка dashboard

Причина повторного показа: `is_ui_relevant_log()` ранее пропускал любые `ERROR` до проверки noise-паттернов. В `utils/runtime_logging.py` ложные строки добавлены в noise-паттерны, а UI сначала вызывает `is_substantive_log()`. Проверка production history: `history_visible_false_errors = 0`.

## Следующий шаг

При добавлении новой партнёрской формы сначала сохранять HTML+PNG артефакт и определять схему полей до написания селекторов.
