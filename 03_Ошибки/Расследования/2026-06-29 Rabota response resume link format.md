# 2026-06-29 Rabota response resume link format

## Симптом

В Google Sheets ссылки на резюме Rabota.ru должны открываться в контексте отклика и вакансии, например:

`https://www.rabota.ru/resume-search/37669170/?source=response&vacancy_id=54309931&response_id=209899152`

Старый fallback мог выгружать только короткую ссылку вида `/resume/{resume_id}`, без `vacancy_id` и `response_id`.

## Зона системы

- `utils/data_processor.py` — `_extract_resume_link()` формирует значение поля `Резюме`.
- `services/leads_service.py` — собирает отклики Rabota.ru и вызывает `normalize_lead()`.
- `modules/sheets_sync.py` — выгружает нормализованное поле `Резюме` в Google Sheets.

## Гипотеза

Для откликов Rabota.ru в raw item уже есть три нужных идентификатора:

- `resume.id`
- `vacancy.id` или `vacancy_id`
- `id` или `response_id`

Если собрать ссылку до fallback-проверки, таблица получит корректный web-route отклика.

## Проверка

- Live-код `utils/data_processor.py` проверен: fallback строил `https://www.rabota.ru/resume/{resume_id}`.
- Добавлен builder для `source_type=response`, который при наличии трёх ID строит `/resume-search/{resume_id}/?source=response&vacancy_id={vacancy_id}&response_id={response_id}`.
- Добавлены regression-тесты:
  - отклик с `resume.id + vacancy.id + response id` получает новый формат;
  - отклик без response context сохраняет старый fallback `/resume/{resume_id}`.

## Наблюдение

Формат ссылки должен формироваться до проверки готовых URL-полей, потому что API Rabota.ru может не отдавать прямой web-url нужного контекста отклика.

## Вывод

Канон для Rabota.ru response-лидов:

`Резюме = https://www.rabota.ru/resume-search/{resume_id}/?source=response&vacancy_id={vacancy_id}&response_id={response_id}`

Fallback `/resume/{resume_id}` допустим только если не хватает `vacancy_id` или `response_id`.

Проверки:

- `python -m pytest tests/test_data_processor.py tests/test_leads_service_sheets_flow.py -q` — `44 passed`.
- Live check вернул точную ссылку из примера пользователя.
- Контейнеры `autolead_bot` и `worker` пересобраны, `/api/health` отвечает `ok`.
- GitHub commit TrafficHub: `898a9a91c Fix Rabota response resume links`.

## Следующий шаг

Новые выгрузки будут получать новый формат. Старые строки в Google Sheets автоматически не переписываются.

Связано: [[Leads service]]
