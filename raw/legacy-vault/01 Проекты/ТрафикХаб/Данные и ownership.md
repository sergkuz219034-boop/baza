# Данные и ownership

## Основные слои данных

- PostgreSQL:
  - control/users/config
  - новый `traffic_hub` слой
- Redis:
  - queue
  - progress
  - stop flags
  - realtime status
- runtime artifacts:
  - user config
  - secrets
  - Rabota tokens
  - worker heartbeat

## Google Sheets contract

Для каждого пользователя существуют свои user-scoped привязки:

- `pending_spreadsheet_id`
- `pending_sheet_name`
- `processed_spreadsheet_id`
- `processed_sheet_name`

Что важно:

- нельзя считать таблицу `admin` глобальной;
- выгрузка и отработка проверяются только относительно settings конкретного пользователя;
- `pending` и `processed` не должны fallback-иться в legacy `google_sheets.spreadsheet_id`.

## Инварианты таблиц

- `pending` / основная таблица:
  - текущие лиды
  - содержит колонку `Резюме`
- `processed` / отработанная:
  - статусы обработки
  - колонки `Статус`, `Дата отработки`, `Офферы`
  - колонки `Резюме` там быть не должно
- строки должны поддерживаться в хронологическом порядке по дате;
- отработка идёт по кандидатам без статуса, а не по текущей дате выгрузки.

## Ownership runtime

- job, progress и stop работают per owner;
- несколько пользователей могут физически делить одну и ту же Google Sheets, но это не отменяет owner-scoped settings;
- любые live smoke лучше делать на debug-owner, а не на рабочих пользователях.
