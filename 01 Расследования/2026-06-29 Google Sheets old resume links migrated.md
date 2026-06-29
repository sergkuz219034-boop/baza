# 2026-06-29 Google Sheets old resume links migrated

## Симптом

Пользователь попросил перевести старые строки в Google Sheets на новый формат поля `Резюме`.

Канон после предыдущего фикса:

`https://www.rabota.ru/resume-search/{resume_id}/?source=response&vacancy_id={vacancy_id}&response_id={response_id}`

Старые строки всё ещё содержали legacy-ссылки:

`https://www.rabota.ru/resume/{resume_id}`

## Зона системы

- `utils/data_processor.py` — канонический builder нового URL
- `autolead_leads` в PostgreSQL — источник `resume_id`, `response_id`, `vacancy_id`
- owner-scoped Google Sheets `pending` workbook / sheet `Все лиды`

## Гипотеза

Старые ссылки можно мигрировать без ручного ввода, если:

1. взять `resume_id` из старого URL в таблице;
2. найти соответствующий lead в `autolead_leads`;
3. восстановить новый `resume-search` URL из `resume_id + vacancy_id + response_id`.

## Проверка

1. Live-код подтвердил, что новый формат строится в `utils/data_processor.py::_extract_resume_link()`.
2. Dry-run по owner-scoped workbook'ам показал:
   - shared workbook `admin + artem`: `747` старых ссылок, из них `743` восстанавливаются однозначно;
   - `alex`: `3720` старых ссылок, из них `3060` восстанавливаются однозначно;
   - `kursmerkusheva@gmail.com`: `1739` старых ссылок, из них `1621` восстанавливаются однозначно.
3. Для матчинга использовались:
   - `resume_id` из старого URL;
   - `phone`, `vacancy`, `lead_date` из строки Google Sheets как уточняющие фильтры;
   - `response_id`, `vacancy_id` из `autolead_leads`.
4. Обновление выполнено одной массовой записью по колонке `Резюме` на каждый workbook, а не поклеточно.
5. После миграции повторный проход показал остаток legacy-ссылок:
   - shared workbook `admin + artem`: `4`
   - `alex`: `660`
   - `kursmerkusheva@gmail.com`: `118`

## Наблюдение

- Миграция затронула только листы `Все лиды`.
- Во вторых workbook'ах, используемых как processed/export surface, колонки `Резюме` в текущей структуре не было, поэтому там переписывать было нечего.
- Невосстановленные строки — это не ambiguous-match. Для них просто не нашлось нужного runtime-контекста в текущем `autolead_leads`.

## Вывод

Массовая миграция старых ссылок выполнена успешно для всех строк, где сохранился runtime-контекст.

Итог обновления:

- `743` строк в shared workbook `admin + artem`
- `3060` строк у `alex`
- `1621` строк у `kursmerkusheva@gmail.com`

Всего обновлено: `5424` строки.

## Следующий шаг

- Если нужно добить оставшиеся `782` legacy-ссылки, потребуется отдельный источник истины:
  - старые логи сбора,
  - архивный runtime snapshot,
  - либо повторное восстановление контекста из Rabota API, если оно вообще возможно.
- Для новых выгрузок отдельная миграция больше не нужна: новый формат уже строится на этапе нормализации лида.
