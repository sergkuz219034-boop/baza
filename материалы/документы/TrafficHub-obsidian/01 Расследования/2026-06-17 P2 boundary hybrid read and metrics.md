# 2026-06-17 P2 boundary hybrid read and metrics

## Симптом

После разметки `P1` active runtime fallback оставалась отдельная ambiguity zone:

- какие SQLite-ветки ещё живут не в runtime write-path, а в read/metrics слое;
- какие из них выглядят как нормальная compatibility-поддержка;
- какие продолжают искажать понимание dashboard/history/analytics contract.

## Зона системы

- live repo `/root/TrafficHub`
- `utils/runtime_repository.py`
- `services/stats_service.py`

## Гипотеза

На `2026-06-17` `P2`-слой уже не определяет основной runtime storage contract, но сохраняет dual-path чтение:

1. `utils/runtime_repository.py` обслуживает owner leads/history/summary через PostgreSQL или SQLite в зависимости от backend flag;
2. `services/stats_service.py` читает postback-метрики только из SQLite path `traffic_hub` БД, если `traffic_settings.database_url` указывает на SQLite.

## Проверка

По live-коду подтверждено:

- `utils/runtime_repository.py` использует `_pg_enabled()` на базе `AUTOLEAD_RUNTIME_LEADS_BACKEND`;
- при `postgres` он читает:
  - `autolead_leads`
  - `autolead_send_history`
  - `autolead_retry_queue`
  - `autolead_run_log`
- те же методы (`list_owned_leads`, `export_owned_leads`, `reset_owned_lead_history`, `get_owned_summary`, `get_owned_history`) сохраняют полноценную SQLite branch;
- `services/stats_service.py` строит `get_summary()` и `get_history()` поверх:
  - `utils.runtime_repository`
  - `utils.database.get_recent_runs()`
  - `utils.database.get_avg_fill_time_ms()`
  - `utils.database.get_retry_queue_size()`
- `services/stats_service.py:get_postback_metrics()` отдельно открывает SQLite connection только если `traffic_hub.config.settings.database_url` начинается с `sqlite:///` или `sqlite+aiosqlite:///`;
- если `traffic_hub` DB URL не SQLite или файл отсутствует, postback-метрики деградируют в нулевой ответ, а не переключаются в PostgreSQL path.

## Наблюдение

### `utils/runtime_repository.py`

Что keep сейчас:

- PostgreSQL read path для owner leads/history/summary;
- read-model boundary как отдельный слой поверх runtime store;
- SQLite branch, если проект официально ещё поддерживает legacy/local runtime read mode.

Что candidate for cleanup:

- dual-path чтение внутри одного модуля без явного разделения на production vs compatibility;
- impression, что dashboard/history логика всё ещё в равной степени ориентирована на SQLite;
- SQLite branch как default reading alternative без жёсткой маркировки legacy-only.

Это не выглядит как критичный production write-risk, но продолжает размывать mental model read-contract.

### `services/stats_service.py`

Что keep сейчас:

- агрегирующий слой для dashboard summary/history;
- использование `runtime_repository` и runtime facade для основной operational статистики.

Что candidate for cleanup:

- `_traffic_db_path()` и `sqlite3.connect(...)` для postback-метрик;
- implicit assumption, что product analytics DB может быть локальным SQLite-файлом;
- отсутствие PostgreSQL-aware branch для `postback_logs` / `conversions`, если live `traffic_hub` БД уже не SQLite.

Это уже не `Autolead runtime` fallback, а отдельный hybrid metrics gap.

## Вывод

Для `P2` boundary на `2026-06-17`:

- `utils/runtime_repository.py` надо описывать как hybrid read-model, а не как часть незавершённой runtime migration;
- `services/stats_service.py` содержит SQLite-only path только для product postback-метрик и потому должен рассматриваться отдельно от `Autolead runtime` storage;
- cleanup `P2` должен идти не как удаление "всего SQLite", а как явное разделение:
  - production read contract
  - legacy/local read fallback
  - product analytics metrics path

## Следующий шаг

1. Поднять `P2 boundary` в краткий канон.
2. Зафиксировать в техдолге, что `runtime_repository` и `stats_service` — это уже не P1 runtime fallback, а hybrid read/metrics stream.
3. Отдельно проверить, какой backend реально использует `traffic_hub` product DB на live-хосте, если понадобится закрывать metrics gap не только документацией.
