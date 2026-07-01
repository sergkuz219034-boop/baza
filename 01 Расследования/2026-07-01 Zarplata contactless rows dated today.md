# 2026-07-01 Zarplata contactless rows dated today

## Симптом

В Google Sheets pending-таблице появились примерно `2600+` строк с датой `01.07.2026`. Визуально строки выглядели как лиды, но у большинства были пустые контакты: `Номер = нету`, `Почта = нету`, пустое поле `Резюме`.

## Зона системы

- `modules/zarplata_api.py`
- `services/leads_service.py`
- Google Sheets pending-таблица `1seCE2MPKZV01LJMvL4CuvSDL7IdG-V_vN6hmqoAcZOs`, лист `Все лиды`
- PostgreSQL таблица `autolead_leads`
- owner-scoped config `zarplata_ru`

## Гипотеза

Зарплата.ру импортировала search-result записи без контактов как полноценные лиды и ставила им текущую дату выгрузки вместо даты резюме/отклика.

## Проверка

Подтверждено на live-сервере:

- У `artem` `zarplata_ru.enabled = false`, поэтому профиль не был источником массовой выгрузки.
- У `admin` `zarplata_ru.enabled = true`, `rabota_ru.period = 30`, pending Google Sheets указывает на тот же документ.
- В PostgreSQL по `lead_date = 01.07.2026` нет `2600+` новых строк: найдены только единичные записи. Значит массовое загрязнение произошло на уровне Google Sheets upload, а не через нормальное сохранение `autolead_leads`.
- В Google Sheets найдено `2623` строки с датой `01.07.2026`; у подавляющей части пустые контактные поля и пустое поле резюме.
- В `modules/zarplata_api.py::normalize_resume()` дата ставилась как `datetime.now(_MSK).strftime("%d.%m.%Y")`.
- В `modules/zarplata_api.py::import_resumes()` фильтр пропускал запись, если было хотя бы `Фио`, даже без `Номер` и `Почта`.

## Наблюдение

Проблема состояла из двух частей:

- `normalize_resume()` превращал найденные старые резюме в лиды с датой текущей выгрузки.
- `import_resumes()` считал name/title-only search results валидными лидами, а `upload_to_sheets()` позже отображал пустые контакты как `нету`.

## Вывод

Root cause подтверждён кодом и runtime-данными: Зарплата.ру search import не отделял контактные резюме от contactless результатов поиска.

После server commit `ba15d7a59` и follow-up `dbe7a30a6` канон такой:

- Зарплата.ру лид сохраняется и выгружается только если есть телефон или email.
- Дата лида берётся из `created_at`, `updated_at`, `response_date` резюме/отклика; текущая дата используется только как fallback.
- В result добавлен счётчик `no_contact_skipped`.
- Добавлен regression test на пропуск contactless search results.

Проверка:

```text
python -m pytest tests/test_zarplata_api.py tests/test_leads_service_sheets_flow.py tests/test_zarplata_owner_guard.py -q
31 passed
```

Контейнеры пересобраны и перезапущены:

- `traffichub_app`
- `traffichub_worker`

Оба контейнера после рестарта healthy.

## Следующий шаг

Существующие ошибочные строки в Google Sheets уже записаны и не удалялись автоматически. Их нужно чистить отдельным подтверждённым действием по критерию: дата `01.07.2026`, source Зарплата.ру/search-like строка, нет телефона, нет email, нет резюме.

## Связанные заметки

- [[Zarplata.ru integration]]
- [[2026-06-29 Unified Rabota and Zarplata dispatch order]]
- [[2026-06-29 Zarplata owner readiness guard]]
