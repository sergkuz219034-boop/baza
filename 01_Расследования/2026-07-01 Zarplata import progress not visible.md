# 2026-07-01 Zarplata import progress not visible

## Симптом

В полном цикле не видно статус выгрузки Зарплата.ру между стартом фазы и итогом. UI выглядит так, будто этап завис или ничего не делает.

## Зона системы

- `services/leads_service.py::run_full_cycle()`
- `modules/zarplata_api.py::run_zarplata_import()`
- `modules/zarplata_api.py::import_resumes()`
- `modules/zarplata_api.py::ZarplataClient.search_all_resumes()`
- `utils/runtime_logging.py::is_ui_relevant_log()`

## Гипотеза

Зарплата.ру пишет только старт и итог, но не пишет промежуточный progress внутри долгого API-обхода страниц откликов и negotiation collections.

## Проверка

- `services/leads_service.py` печатает `▶ Фаза 2.1: Выгрузка лидов с Зарплата.ру`.
- `modules/zarplata_api.py::run_zarplata_import()` печатал `▶ Зарплата.ру: сбор резюме` и финальный `✓ Зарплата.ру: найдено ..., отклики ..., в Sheets добавлено ...`.
- `ZarplataClient.search_all_resumes()` обходил страницы без пользовательского progress.
- `import_resumes()` обходил active vacancies и negotiation collections без пользовательского progress.
- `utils/runtime_logging.py` уже пропускает строки с substring `Зарплата.ру:`, поэтому проблема была не в фильтре UI.

## Наблюдение

В отличие от Rabota.ru, где после нескольких итераций уже были отдельные realtime/status строки, у Зарплата.ру долгие участки API-работы оставались невидимыми. Это создавало ложное ощущение зависания.

## Вывод

Нужно показывать бизнес-понятный progress Зарплата.ру, но не возвращать технический шум. Канон: видимы старт откликов, throttled page progress, проверка вакансий, throttled negotiation progress и итог.

Product commit `cacb4735c Show Zarplata import progress in logs`:

- `search_all_resumes()` печатает `Зарплата.ру: отклики загружены: N (страница X/Y)` на первой, каждой 5-й и финальной странице;
- `import_resumes()` печатает `Зарплата.ру: начинаю загрузку откликов`;
- `import_resumes()` печатает `Зарплата.ру: проверяю вакансии: N`;
- `import_resumes()` печатает `Зарплата.ру: переговоры загружены: N (...)` на первой, каждой 5-й и финальной странице коллекций;
- tests закрепляют видимость этих строк через `is_ui_relevant_log()`.

Live-проверка 2026-07-01:

- GitHub Actions `CI` и `Build and Push Docker Image` зелёные для `cacb4735c`;
- пересозданы `traffichub_app` и `traffichub_worker`;
- `/api/health` вернул `status=ok`;
- внутри live-контейнера `is_ui_relevant_log()` вернул `True` для новых progress-строк Зарплата.ру.

## Следующий шаг

Если UI снова не показывает прогресс Зарплата.ру, сначала проверить наличие строк в worker/app logs, затем `utils/runtime_logging.py`, потому что frontend отдельно не фильтрует эти строки.
