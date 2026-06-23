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
- `access_token`
- `refresh_token`
- `enabled` — включает сбор резюме Зарплата.ру в общем workflow вкладки `Обзор`.
- `enable_form_fill` — разрешает ли лидам Зарплата.ру попадать в общую очередь заполнения анкет.
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
10. Если `enable_form_fill=false`, строки получают `Статус = заполнение выключено`; общий sender берёт только строки с пустым статусом, поэтому такие лиды не заполняются.

## Почему запуск через Обзор

Вкладки источников (`Зарплата.ру`, `SuperJob`, Rabota.ru-настройки) не должны конкурировать с основными рабочими кнопками. Каноническая точка запуска для оператора — `Обзор`: `Выгрузка`, `Рассылка`, `Полный цикл`. Это снижает риск двойного запуска и делает логику одинаковой для источников.

## Ограничения

- Контакты зависят от прав токена и ответа API Зарплата.ру.
- Negotiations/приглашения пока не реализованы.
- App-token через `client_credentials` может быть недостаточен для контактных данных; тогда нужен employer OAuth token через `authorization_code`.
- Если `enable_form_fill=false`, уже выгруженные строки не попадут в заполнение, пока их статус в Google Sheets не будет очищен вручную или повторной логикой.

## Связанные заметки

- [[2026-06-22 Zarplata.ru независимый модуль и отключение TrafficHub для user]]
- [[2026-06-23 Zarplata.ru workflow через Обзор и переключатели]]
- [[Отключение embedded TrafficHub для user]]
