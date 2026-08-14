# 2026-06-30 Zarplata vacancies in offer binding modal

## Симптом

В модалке оффера в блоке `Привязка к вакансиям` отображались только вакансии `Rabota.ru` и локальные name-based привязки. Пользователь попросил добавить туда вакансии `Зарплата.ру`.

## Зона системы

- `dashboard/app.js`
- `api/routers/offers.py`
- `tests/test_offers_import_export.py`
- endpoint: `GET /api/offers/binding_candidates`
- live container: `traffichub_app`

## Гипотеза

Backend уже умеет объединять Rabota.ru и Зарплата.ру в общем endpoint `GET /api/offers/vacancies`, но модалка оффера использует старый endpoint `GET /api/offers/binding_candidates`, где нет секции `zarplata`.

## Проверка

- `tests/test_offers_import_export.py::test_vacancies_endpoint_combines_rabota_and_zarplata` подтверждал, что `/api/offers/vacancies` отдаёт оба источника.
- `dashboard/app.js::openOfferModal()` грузил `/api/offers/binding_candidates` и читал только `res.rabota` / `res.sheets`.
- `api/routers/offers.py::get_binding_candidates()` до фикса возвращал только `rabota` и `sheets`.
- `modules/zarplata_api.py::normalize_resume()` пишет название вакансии в поле `Вакансия`, поэтому для офферов Зарплата.ру безопаснее использовать `vacancy_names`, а не `vacancy_ids`.

## Наблюдение

Зарплата.ру вакансии не отсутствовали в интеграции целиком; они отсутствовали именно в старом binding endpoint и UI-рендере модалки оффера.

## Вывод

Канон для offer binding modal:

- Rabota.ru вакансии остаются ID-based (`vacancy_ids`);
- Зарплата.ру вакансии показываются отдельной группой `Zarplata.ru`;
- выбранные Зарплата.ру вакансии сохраняются как name-based bindings (`vacancy_names`), потому что matching в full-cycle уже умеет нормализовать названия вакансий.

Фикс product commit `20621b069`:

- `GET /api/offers/binding_candidates` возвращает `zarplata`;
- `dashboard/app.js::openOfferModal()` рендерит группу `Zarplata.ru`;
- regression test: `test_binding_candidates_include_zarplata_vacancies`.

## Следующий шаг

Если понадобится ID-based matching для Зарплата.ру, сначала нужно расширить schema `offer_mapping`, потому что текущий `vacancy_ids: list[int]` исторически привязан к Rabota.ru.
