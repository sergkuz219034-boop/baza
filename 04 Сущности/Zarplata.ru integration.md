# Zarplata.ru integration

## Назначение

Интеграция собирает резюме из официального API Зарплата.ру и приводит их к общему формату лидов Autolead.

## Подтверждённые файлы

- `modules/zarplata_api.py` — API-клиент, OAuth helpers, нормализация резюме, импорт в БД и Google Sheets.
- `api/routers/zarplata.py` — HTTP endpoints для статуса, проверки, OAuth и запуска поиска.
- `api/routers/settings_core.py` — owner-scoped mapping полей `zarplata_ru`.
- `api/routers/jobs.py` — команда `zarplata`.
- `traffic_hub/services/job_runner.py` — выполнение команды `zarplata` worker-процессом и подключение Зарплата.ру к общим командам `upload`/`run`.
- `services/leads_service.py` — thin-wrapper `run_zarplata_import()`.

## Настройки

Секция owner-scoped config: `zarplata_ru`.

Поля:

- `client_id`
- `client_secret`
- `redirect_uri`
- `access_token` — user OAuth token для `GET /resumes`.
- `app_access_token` — отдельный token приложения через `client_credentials`; не должен подменять user token.
- `refresh_token`
- `enabled` — включает сбор резюме Зарплата.ру в общем workflow вкладки `Обзор`.
- `enable_form_fill` — legacy/внутренний флаг допуска лидов Зарплата.ру к общей очереди заполнения анкет. В текущем UI отдельного переключателя нет: один тумблер `Режим Зарплата.ру` означает и сбор, и заполнение.
- `enable_auto_invite` — включает автоприглашения через официальный API Зарплата.ру. Это отдельный флаг от Rabota `enable_auto_invite`.
- `query`
- `area`
- `per_page`

## API

Подтверждённые endpoints TrafficHub:

- `GET /api/zarplata/status`
- `GET /api/zarplata/auth-url`
- `POST /api/zarplata/token`
- `POST /api/zarplata/app-token`
- `POST /api/zarplata/check`
- `POST /api/zarplata/search`

Подтверждённые endpoints Зарплата.ру из `openapi.yml`:

- `https://hr.zarplata.ru/oauth/authorize`
- `POST https://api.zarplata.ru/token`
- `GET https://api.zarplata.ru/me`
- `GET https://api.zarplata.ru/resumes`
- `POST https://api.zarplata.ru/negotiations/phone_interview` — приглашение соискателя на вакансию.

## Поток данных

1. Пользователь сохраняет настройки во вкладке `Зарплата.ру`.
2. Backend сохраняет данные в owner-scoped `zarplata_ru`.
3. Пользователь запускает `Выгрузка` или `Полный цикл` во вкладке `Обзор`.
4. `traffic_hub/services/job_runner.py` проверяет owner readiness через `_zarplata_ready_for_owner()`.
5. В команде `Полный цикл` `services/leads_service.py::run_full_cycle()` сначала выполняет Rabota.ru: сбор и выгрузку в Google Sheets.
6. Если `enabled=true`, заполнены `client_id/client_secret` и есть user OAuth `access_token`, `run_full_cycle()` вызывает `modules.zarplata_api.run_zarplata_import()` сразу после выгрузки Rabota.ru и до общей рассылки.
7. Лиды Зарплата.ру выгружаются в ту же pending-таблицу Google Sheets, что и Rabota.ru, без отдельной рассылки.
8. Фаза рассылки загружает общую pending-очередь из Google Sheets и обрабатывает вместе лиды Rabota.ru и Зарплата.ру.
9. API `/resumes` возвращает резюме.
10. `normalize_resume()` приводит запись к колонкам Autolead.
11. `save_leads()` сохраняет лиды в БД.
12. `upload_to_sheets()` выгружает лиды в уже настроенную Google Sheets.
13. Backend нормализует старые настройки: если `enabled=true`, то импорт считается разрешённым для заполнения, даже если в legacy config остался `enable_form_fill=false`.
14. Старый статус `Статус = заполнение выключено` считается legacy/dead-state для уже выгруженных строк. Новые строки при включённом источнике не должны получать этот статус.
15. Если `zarplata_ru.enable_auto_invite=true`, общий sender в `modules/vbiv_bot.py` для лидов `_source_type=zarplata` вызывает `ZarplataClient.invite_applicant()`.
16. Для приглашения используются `resume_id` из `_source_id` / `_raw_data.external_resume_id` и `vacancy_id` из `_zarplata_vacancy_id`.
17. История Zarplata-приглашений хранится отдельно от Rabota: `autolead_platform_invite_history`, ключ `platform=zarplata + resume_id + vacancy_id`.

После commit `ba15d7a59` добавлено обязательное правило качества лида Зарплата.ру:

- `modules/zarplata_api.py::import_resumes()` сохраняет и выгружает только записи, у которых есть телефон или email.
- Search-result записи без контактов считаются техническим шумом API и учитываются только в счётчике `no_contact_skipped`.
- `modules/zarplata_api.py::normalize_resume()` больше не ставит текущую дату всем найденным резюме. Дата берётся из `response_date`, `created_at`, `updated_at`, `published_at`, `modified_at` или из `_zarplata_negotiation.created_at/updated_at`; текущая дата используется только как fallback.
- Это правило введено после расследования [[2026-07-01 Zarplata contactless rows dated today]], где Google Sheets получил `2600+` строк с датой выгрузки `01.07.2026` и пустыми контактами.

Если `enabled=true`, но `access_token` пустой, `run_zarplata_import()` после commit `75a1a619c` не падает исключением и не останавливает общий цикл. Он пишет в рабочий лог, что пользовательский OAuth token не подключён, возвращает `reason=no_access_token` и пропускает выгрузку.

После commit `d8e0206f4` канон запуска жёстче:

`ready = enabled && client_id && client_secret && access_token`

Это правило применяется:

- в `traffic_hub/services/job_runner.py` для команд `upload`, `run`, `automode`;
- в `modules/zarplata_api.py` для прямого запуска, где отсутствие `client_id/client_secret` возвращает `reason=missing_app_credentials`.

После commit `d2c4c0256` канон порядка такой:

`Rabota.ru сбор -> Rabota.ru Google Sheets -> Зарплата.ру Google Sheets -> общая рассылка из pending-таблицы`

Причина: рассылка должна быть единой для обоих источников. Если Зарплата.ру запускается до Rabota.ru или отдельной веткой, общий sender может не увидеть свежие строки обоих источников в одном проходе.

## Логи во вкладке Обзор

- Подтверждено кодом: при запуске через `traffic_hub/services/job_runner.py` stdout Zarplata-модуля перенаправляется в owner-scoped runtime log через `_OwnerLogStream`.
- Подтверждено кодом: `dashboard/app.js -> isVisibleLogMessage()` не скрывает строки `Зарплата.ру`, поэтому они должны быть видны в `Обзор`.
- Практический смысл: отдельной вкладке не нужен свой особый лог-контур; Zarplata использует общий pipeline `Обзор`.

## Почему запуск через Обзор

Вкладки источников (`Зарплата.ру`, `SuperJob`, Rabota.ru-настройки) не должны конкурировать с основными рабочими кнопками. Каноническая точка запуска для оператора — `Обзор`: `Выгрузка`, `Рассылка`, `Полный цикл`. Это снижает риск двойного запуска и делает логику одинаковой для источников.

## Ограничения

- Контакты зависят от прав токена и ответа API Зарплата.ру.
- Автоприглашения реализованы через `POST /negotiations/phone_interview`, но live-успех зависит от прав конкретного user OAuth token. API может вернуть `403`, если нет доступа к вакансии, резюме или платному employer API действию.
- `app_access_token` через `client_credentials` не подходит для поиска резюме, если API требует user OAuth token. Для `GET /resumes` нужен токен, полученный через `authorization_code`.
- Legacy-runtime уже ломался из-за смешения `app token` и `user token` в одном поле; после фикса эти поля разделены, а старые `APPL...` токены автоматически мигрируются из `access_token` в `app_access_token`.
- На live-профиле `Artem` 2026-06-25 подтверждено: app-token даёт `403 user_auth_expected` на `/resumes`; реальная выгрузка невозможна до получения user OAuth token работодателя.
- Старые строки, уже выгруженные до фикса со статусом `заполнение выключено`, не попадут в заполнение, пока их статус в Google Sheets не будет очищен вручную или отдельной миграцией по конкретной вкладке.
- Если в owner-scoped config снова появится `enabled=true` вместе с `enable_form_fill=false`, `/api/settings/zarplata` должен нормализовать это состояние при следующем сохранении.
- Уже записанные в Google Sheets contactless строки не удаляются кодовым фиксом автоматически. Их нужно чистить отдельной подтверждённой операцией по конкретному листу и критериям, чтобы не удалить реальные лиды.

## Связанные заметки

- [[2026-06-22 Zarplata.ru независимый модуль и отключение TrafficHub для user]]
- [[2026-06-23 Zarplata.ru workflow через Обзор и переключатели]]
- [[2026-06-25 Zarplata.ru app token ломал поиск резюме]]
- [[2026-06-29 Zarplata form fill disabled status]]
- [[2026-06-29 Zarplata owner readiness guard]]
- [[2026-06-29 Unified Rabota and Zarplata dispatch order]]
- [[2026-06-30 возможность автоприглашений Zarplata.ru]]
- [[2026-07-01 Zarplata contactless rows dated today]]
- [[Отключение embedded TrafficHub для user]]
