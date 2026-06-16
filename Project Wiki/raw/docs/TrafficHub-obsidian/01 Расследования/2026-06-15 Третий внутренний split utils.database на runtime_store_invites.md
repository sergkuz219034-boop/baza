# 2026-06-15 Третий внутренний split `utils.database` на `runtime_store_invites`

## Симптом

После выноса logs и delivery-блоков `utils/database.py` всё ещё держал invite-сценарии:

- `invite_history`
- `invite_message_state`

Это сохраняло лишнюю связанность legacy SQLite store в одном файле.

## Зона системы

- legacy Autolead runtime store
- `utils/database.py`
- invite flow
- UI fallback для последнего текста приглашения

## Гипотеза

Invite-блок можно вынести в отдельный internal module без смены внешнего API, если оставить `utils.database` как compatibility facade.

## Проверка

На live source сервера:

- добавлен `utils/runtime_store_invites.py`;
- `utils/database.py` переведён на делегирование для функций:
  - `load_invite_history`
  - `add_invite_history`
  - `save_last_invite_message`
  - `load_last_invite_message`
  - `clear_invite_history`

Прогнаны проверки:

- `python3 -m compileall -q utils/runtime_store_invites.py utils/database.py api traffic_hub services modules config main.py`
- `python3 -m pytest -q tests/test_database.py -q`

## Наблюдение

- `compileall` прошёл.
- `tests/test_database.py` прошёл полностью.
- Внешние импорты из `utils.database` сохранены.
- Storage физически не менялся: это тот же legacy SQLite runtime.

## Вывод

Третий безопасный internal split подтверждён. `utils.database.py` продолжает уменьшаться по ответственностям без большой миграции и без смены runtime-контракта.

## Следующий шаг

1. Оценить, стоит ли следующим шагом выделять `control_sync_queue`.
2. Не переносить SQLite в PostgreSQL до завершения decomposition и repository boundaries.
3. Продолжать фиксировать каждый split в docs и wiki сразу после проверки.
