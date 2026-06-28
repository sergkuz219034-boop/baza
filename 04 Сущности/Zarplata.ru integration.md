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

## Поток данных

1. Пользователь сохраняет настройки во вкладке `Зарплата.ру`.
2. Backend сохраняет данные в owner-scoped `zarplata_ru`.
3. Пользователь запускает `Выгрузка` или `Полный цикл` во вкладке `Обзор`.
4. `traffic_hub/services/job_runner.py` проверяет `zarplata_ru.enabled`.
5. Если сбор включён, worker вызывает `modules.zarplata_api.run_zarplata_import()` до основного Rabota.ru flow.
6. API `/resumes` возвращает резюме.
7. `normalize_resume()` приводит запись к колонкам Autolead.
8. `save_leads()` сохраняет лиды в БД.
9. `upload_to_sheets()` выгружает лиды в уже настроенную Google Sheets.
10. Backend нормализует старые настройки: если `enabled=true`, то импорт считается разрешённым для заполнения, даже если в legacy config остался `enable_form_fill=false`.
11. Старый статус `Статус = заполнение выключено` считается legacy/dead-state для уже выгруженных строк. Новые строки при включённом источнике не должны получать этот статус.

Если `enabled=true`, но `access_token` пустой, `run_zarplata_import()` после commit `75a1a619c` не падает исключением и не останавливает общий цикл. Он пишет в рабочий лог, что пользовательский OAuth token не подключён, возвращает `reason=no_access_token` и пропускает выгрузку.

## Логи во вкладке Обзор

- Подтверждено кодом: при запуске через `traffic_hub/services/job_runner.py` stdout Zarplata-модуля перенаправляется в owner-scoped runtime log через `_OwnerLogStream`.
- Подтверждено кодом: `dashboard/app.js -> isVisibleLogMessage()` не скрывает строки `Зарплата.ру`, поэтому они должны быть видны в `Обзор`.
- Практический смысл: отдельной вкладке не нужен свой особый лог-контур; Zarplata использует общий pipeline `Обзор`.

## Почему запуск через Обзор

Вкладки источников (`Зарплата.ру`, `SuperJob`, Rabota.ru-настройки) не должны конкурировать с основными рабочими кнопками. Каноническая точка запуска для оператора — `Обзор`: `Выгрузка`, `Рассылка`, `Полный цикл`. Это снижает риск двойного запуска и делает логику одинаковой для источников.

## Ограничения

- Контакты зависят от прав токена и ответа API Зарплата.ру.
- Negotiations/приглашения пока не реализованы.
- `app_access_token` через `client_credentials` не подходит для поиска резюме, если API требует user OAuth token. Для `GET /resumes` нужен токен, полученный через `authorization_code`.
- Legacy-runtime уже ломался из-за смешения `app token` и `user token` в одном поле; после фикса эти поля разделены, а старые `APPL...` токены автоматически мигрируются из `access_token` в `app_access_token`.
- На live-профиле `Artem` 2026-06-25 подтверждено: app-token даёт `403 user_auth_expected` на `/resumes`; реальная выгрузка невозможна до получения user OAuth token работодателя.
- Старые строки, уже выгруженные до фикса со статусом `заполнение выключено`, не попадут в заполнение, пока их статус в Google Sheets не будет очищен вручную или отдельной миграцией по конкретной вкладке.
- Если в owner-scoped config снова появится `enabled=true` вместе с `enable_form_fill=false`, `/api/settings/zarplata` должен нормализовать это состояние при следующем сохранении.

## Связанные заметки

- [[2026-06-22 Zarplata.ru независимый модуль и отключение TrafficHub для user]]
- [[2026-06-23 Zarplata.ru workflow через Обзор и переключатели]]
- [[2026-06-25 Zarplata.ru app token ломал поиск резюме]]
- [[2026-06-29 Zarplata form fill disabled status]]
- [[Отключение embedded TrafficHub для user]]
