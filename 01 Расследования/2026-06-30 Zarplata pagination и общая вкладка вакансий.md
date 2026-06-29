# 2026-06-30 Zarplata pagination и общая вкладка вакансий

## Симптом

- В Zarplata.ru собирались не все лиды.
- Вкладка называлась `Вакансии Rabota.ru`, хотя в ней должны быть вакансии нескольких источников.

## Зона системы

- `/root/TrafficHub/modules/zarplata_api.py`
- `/root/TrafficHub/api/routers/offers.py`
- `/root/TrafficHub/dashboard/index.html`
- `/root/TrafficHub/dashboard/app.js`
- Официальная документация: `https://api.zarplata.ru/openapi/redoc`

## Гипотеза

- Потеря лидов связана с тем, что код читает только первую страницу `GET /resumes`.
- Вкладка вакансий должна быть агрегатором нескольких источников, а не Rabota-only экраном.

## Проверка

- Проверен OpenAPI spec `https://api.zarplata.ru/openapi/specification/zarplata`.
- Для `GET /resumes` подтверждены параметры `page`, `per_page` и ответные поля `pages`, `found`.
- Для активных вакансий работодателя подтверждён endpoint `GET /employers/{employer_id}/vacancies/active`.

## Наблюдение

- До фикса `import_resumes()` вызывал `client.search_resumes(...)` один раз.
- `per_page` был ограничен `50`, хотя для `/resumes` spec допускает `100`.
- `/api/offers/vacancies` возвращал только Rabota.ru.

## Вывод

- Root cause неполного сбора Zarplata.ru: отсутствие постраничного обхода.
- Исправление: `ZarplataClient.search_all_resumes()` + `import_resumes()` использует все страницы.
- Вкладка переименована в `Вакансии`.
- `/api/offers/vacancies` теперь агрегирует Rabota.ru и Zarplata.ru, а UI показывает `source_label`.
- Массовые приглашения в этой вкладке остаются только для Rabota.ru; Zarplata.ru карточки read-only.

## Следующий шаг

- Если потребуется приглашение по Zarplata.ru, делать отдельный контур по официальным endpoints откликов/приглашений, не смешивая с Rabota.ru bulk invite.
