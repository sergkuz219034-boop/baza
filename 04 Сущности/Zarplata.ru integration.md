# Zarplata.ru integration

## Назначение

Интеграция собирает резюме из официального API Зарплата.ру и приводит их к общему формату лидов Autolead.

## Подтверждённые файлы

- `modules/zarplata_api.py` — API-клиент, OAuth helpers, нормализация резюме, импорт в БД и Google Sheets.
- `api/routers/zarplata.py` — HTTP endpoints для статуса, проверки, OAuth и запуска поиска.
- `api/routers/settings_core.py` — owner-scoped mapping полей `zarplata_ru`.
- `api/routers/jobs.py` — команда `zarplata`.
- `traffic_hub/services/job_runner.py` — выполнение команды `zarplata` worker-процессом.
- `services/leads_service.py` — thin-wrapper `run_zarplata_import()`.

## Настройки

Секция owner-scoped config: `zarplata_ru`.

Поля:

- `client_id`
- `client_secret`
- `redirect_uri`
- `access_token`
- `refresh_token`
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
3. Кнопка `Найти и выгрузить` ставит job `zarplata` в очередь.
4. Worker вызывает `modules.zarplata_api.run_zarplata_import()`.
5. API `/resumes` возвращает резюме.
6. `normalize_resume()` приводит запись к колонкам Autolead.
7. `save_leads()` сохраняет лиды в БД.
8. `upload_to_sheets()` выгружает лиды в уже настроенную Google Sheets.

## Ограничения

- Контакты зависят от прав токена и ответа API Зарплата.ру.
- Negotiations/приглашения пока не реализованы.
- App-token через `client_credentials` может быть недостаточен для контактных данных; тогда нужен employer OAuth token через `authorization_code`.

## Связанные заметки

- [[2026-06-22 Zarplata.ru независимый модуль и отключение TrafficHub для user]]
- [[Отключение embedded TrafficHub для user]]
