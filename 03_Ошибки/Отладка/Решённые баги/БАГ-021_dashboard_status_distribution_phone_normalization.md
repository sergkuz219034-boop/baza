# БАГ-021: analytics `status_distribution` показывал почти все лиды как `new`

## Симптом

В analytics summary/history часть пользователей видела противоречивую картину:

- `processed_today` и `offers_today` были ненулевые;
- но `status_distribution` в analytics показывал почти все лиды как `new`;
- из-за этого блок `Успешных отправок / Лидов без отправки / Лидов с ошибкой` был искажён.

На live это проявлялось у `admin`, `artem`, `kursmerkusheva@gmail.com`.

## Зона системы

- `utils/runtime_repository.py`
- PostgreSQL ветка `get_owned_history()`
- `services/stats_service.py`

## Гипотеза

Owner-scoped history в PostgreSQL read-model сопоставлял lead rows со статусами отправки по сырому `phone`, хотя в `autolead_leads` и `autolead_send_history` телефоны могли храниться в разных форматах:

- `+7...`
- `8...`
- `10-digit normalized`

## Проверка

- В `utils/runtime_repository.py` до фикса:
  - `_pg_status_maps()` строил map по сырому `phone`;
  - `_decorate_lead_row()` также искал статус по сырому `phone`.
- При этом в runtime встречались разные phone-форматы между `autolead_leads` и `autolead_send_history`.
- После фикса:
  - в `runtime_repository.py` добавлен локальный `_normalize_phone_key()`;
  - `_pg_status_maps()` теперь сохраняет `sent/retry` map по нормализованному номеру;
  - `_decorate_lead_row()` тоже сравнивает по нормализованному номеру.
- Добавлены тесты:
  - `tests/test_runtime_repository.py`
- Контейнерный pytest на live:
  - `tests/test_stats_service.py`
  - `tests/test_runtime_repository.py`
  - `tests/test_leads_service_sheets_flow.py`
  - `tests/test_config_merge.py`
- Результат: `21 passed`.

## Наблюдение

Live-проверка после deploy `59949a1`:

- `admin`
  - `total_leads=85`
  - `status_distribution={sent: 48, error: 0, new: 37}`
- `artem`
  - `total_leads=663`
  - `status_distribution={sent: 32, error: 0, new: 631}`
- `kursmerkusheva@gmail.com`
  - `total_leads=493`
  - `status_distribution={sent: 172, error: 0, new: 321}`

До фикса эти owner-срезы выглядели как почти полностью `new`, несмотря на реальные отправки в `autolead_send_history`.

`alex` после фикса по-прежнему имеет:

- `total_leads=1165`
- `status_distribution={sent: 0, error: 0, new: 1165}`

Это уже не bug в phone matching, а реальный runtime-факт: в его owner-scoped `autolead_send_history` нет отправок.

## Вывод

Проблема была в PG analytics read-model, а не в frontend.

После фикса:

- analytics status counters читаются по нормализованному номеру;
- текущие и будущие owner-аналитики больше не должны превращать отправленные лиды в `new` только из-за phone-format mismatch;
- если у конкретного пользователя `sent=0`, это теперь скорее факт его owner-scoped runtime-данных, а не ошибка сопоставления.

## Следующий шаг

- если нужно восстанавливать аналитику `alex`, расследовать уже не `status_distribution`, а отсутствие owner-scoped записей в `autolead_send_history`;
- при новых баг-репортах по analytics сначала различать:
  - config scope bug;
  - phone normalization bug;
  - реальное отсутствие owner-scoped runtime-данных.
