# 2026-06-16 Мигрировать Autolead runtime поэтапно начиная с логов

## Проблема

TrafficHub уже использует PostgreSQL для нового слоя и control/auth, но legacy Autolead runtime продолжает хранить часть operational state в SQLite. Полный одномоментный перенос рискован: `leads`, `send_history`, `retry_queue` участвуют в выгрузке, рассылке, retry и full cycle.

## Контекст

Подтверждено кодом на сервере:

- `utils/database.py` — фасад legacy runtime storage.
- `utils/runtime_store_logs.py` — SQLite-backed `app_log/run_log`.
- `utils/runtime_store_delivery.py` — SQLite-backed `send_history/retry_queue`.
- `utils/runtime_store_leads.py` — SQLite-backed `leads`.
- `docker-compose.yml` передаёт `DATABASE_URL` в `autolead_bot` и `worker`.

## Решение

Мигрировать Autolead runtime поэтапно, начиная с логов:

1. `app_log/run_log` перевести на PostgreSQL через `AUTOLEAD_RUNTIME_LOGS_BACKEND=postgres`.
2. `send_history` перевести на PostgreSQL через `AUTOLEAD_RUNTIME_DELIVERY_BACKEND=postgres`.
3. Сохранить SQLite fallback.
4. Не менять public API `utils.database`.
5. `retry_queue` перевести на PostgreSQL в том же delivery backend.
6. `leads` перевести на PostgreSQL отдельным backend `AUTOLEAD_RUNTIME_LEADS_BACKEND=postgres`.
7. Перевести `utils/runtime_repository.py` на PostgreSQL-aware reads, иначе dashboard/bridge продолжат смотреть в SQLite.
8. `autofit_seen` перевести на PostgreSQL через `AUTOLEAD_RUNTIME_AUTOFIT_BACKEND=postgres`.
9. `invite_history` и `invite_message_state` перевести на PostgreSQL через `AUTOLEAD_RUNTIME_INVITES_BACKEND=postgres`.
10. `control_sync_queue` перевести на PostgreSQL через `AUTOLEAD_RUNTIME_CONTROL_SYNC_BACKEND=postgres`.
11. Maintenance-функции сделать PostgreSQL-aware, чтобы очистка и prune не работали только по SQLite.
12. SQLite оставить как fallback/test backend до отдельного удаления legacy-совместимости.

## Последствия

Плюсы:

- меньше зависимости observability от SQLite;
- dashboard logs/run history можно читать из PostgreSQL;
- dashboard send history/dedup можно читать из PostgreSQL;
- retry/full cycle использует PostgreSQL для очереди повторов;
- core leads cache и dashboard/bridge lists используют PostgreSQL;
- автоподбор использует PostgreSQL для `autofit_seen`;
- автоприглашения используют PostgreSQL для `invite_history` и последнего текста приглашения;
- background control sync использует PostgreSQL для очереди `control_sync_queue`;
- maintenance cleanup/prune работает по PostgreSQL при production env;
- появляется рабочий шаблон миграции для остальных таблиц;
- worker и web используют один backend через compose env.

Минусы:

- SQLite fallback остаётся в коде, поэтому его нельзя удалять без отдельного этапа;
- schema init всё ещё создаёт SQLite-таблицы для fallback/test;
- unit-тесты должны явно отключать PostgreSQL runtime env, если проверяют SQLite fallback.

## Альтернативы

- Полный перенос всего SQLite runtime сразу: отклонено как слишком рискованное для production Autolead.
- Оставить SQLite навсегда: отклонено, потому что это сохраняет два источника истины и усложняет multi-worker/multi-user эксплуатацию.
- Сначала переносить `leads`: отложено, потому что это более рискованно для выгрузки и dedup.
