# 2026-07-01 Zarplata log spam

## Симптом

Во вкладке логов Autolead Зарплата.ру писала много однотипных строк:

- `Зарплата.ру: отклики загружены: ... (страница .../...)`

На длинной выгрузке это забивало dashboard history и визуально отличалось от Rabota.ru.

## Зона системы

- live repo: `/root/TrafficHub`
- модуль: `modules/zarplata_api.py`
- тесты: `tests/test_zarplata_api.py`
- runtime-контейнеры: `traffichub_app`, `traffichub_worker`

## Гипотеза

Zarplata.ru печатает page-by-page progress обычным `print()`, а dashboard сохраняет stdout как постоянные log rows. Rabota.ru уже использует transient TTY-spinner и не пишет такой progress в non-TTY dashboard logs.

## Проверка

- В `modules/zarplata_api.py::_print_zarplata_page_progress()` был прямой `print(...)`.
- В блоке загрузки переговоров был прямой `print(...)` каждые 5 страниц.
- В `modules/rabota_api.py` аналогичный progress ограничен интерактивным TTY.

## Наблюдение

Dashboard работает не как интерактивный терминал: stdout превращается в persistent строки UI-лога. Поэтому любой page-progress через `print()` становится спамом.

## Вывод

Zarplata.ru progress переведён на TTY-only transient output:

- в non-TTY режиме page-progress не печатается;
- в интерактивном терминале строка перерисовывается через `\r`;
- dashboard logs остаются только со смысловыми строками старта, итогов и ошибок.

Product commit: `fc23458dc fix: suppress zarplata page progress log spam`.

## Следующий шаг

Для новых long-running импортов запрещено печатать page-by-page progress обычным `print()` в runtime-коде. Если нужен прогресс, использовать TTY-only spinner или owner-scoped realtime status без записи каждой страницы в историю логов.
