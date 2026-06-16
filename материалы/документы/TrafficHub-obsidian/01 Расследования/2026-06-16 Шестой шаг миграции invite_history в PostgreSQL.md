# 2026-06-16 Шестой шаг миграции invite_history в PostgreSQL

## Симптом

После миграции логов, истории рассылок, retry, leads и `autofit_seen` SQLite оставался active runtime store для автоприглашений: `invite_history` и `invite_message_state`.

## Зона системы

- `utils/database.py`
- `utils/runtime_store_invites.py`
- `modules/vbiv_bot.py`
- `api/routers/offers.py`
- `api/routers/settings_maintenance.py`
- таблицы SQLite `invite_history`, `invite_message_state`
- новые таблицы PostgreSQL `autolead_invite_history`, `autolead_invite_message_state`

## Гипотеза

Autolead invites можно перенести через новый PostgreSQL backend без изменения внешнего API, потому что все основные потребители используют фасад `utils.database`.

## Проверка

- Добавлен backend `utils/runtime_store_pg_invites.py`.
- В `utils/database.py` добавлено переключение через `AUTOLEAD_RUNTIME_INVITES_BACKEND=postgres`.
- В `docker-compose.yml` добавлена переменная `AUTOLEAD_RUNTIME_INVITES_BACKEND`.
- Созданы таблицы:
  - `autolead_invite_history`;
  - `autolead_invite_message_state`.
- Данные перенесены из SQLite в PostgreSQL.
- Выполнен rebuild/restart `autolead_bot` и `worker`.
- Проверены `docker ps`, `/api/health`, runtime write/read и unit-тесты.

## Наблюдение

Runtime-факты на сервере:

- `autolead_server_bot` — `healthy`.
- `traffichub_worker` — `healthy`.
- `/api/health` вернул `status=ok`.
- SQLite `invite_history`: `108` строк.
- PostgreSQL `autolead_invite_history`: `108` строк после очистки тестового owner.
- SQLite `invite_message_state`: `1` строка.
- PostgreSQL `autolead_invite_message_state`: `1` строка.

Сводка `autolead_invite_history`:

| owner_username | count |
|---|---:|
| admin | 50 |
| artem | 58 |

Во время проверки один раз unit-тесты были запущены с production PG backend env. Это загрязнило PG тестовым owner `test_user`. Записи удалены из runtime PG-таблиц:

- `autolead_run_log`: 1;
- `autolead_send_history`: 1;
- `autolead_retry_queue`: 1;
- `autolead_leads`: 4;
- `autolead_autofit_seen`: 1;
- `autolead_invite_history`: 1;
- `autolead_invite_message_state`: 1.

После корректного запуска с отключёнными runtime backend env:

- `tests/test_database.py tests/test_retry_queue_matching.py` — `39 passed`.

## Вывод

`invite_history` и `invite_message_state` переведены в PostgreSQL. Внешний API `utils.database` сохранён. SQLite fallback сохранён.

Оставшийся active SQLite runtime:

- `control_sync_queue`;
- maintenance-prune код, который ещё знает про SQLite-таблицы.

## Следующий шаг

Перенести `control_sync_queue` в PostgreSQL или подтвердить, что она больше не нужна как active queue после PostgreSQL-first control store.
