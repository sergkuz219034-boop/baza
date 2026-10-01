# Статус и roadmap

## Текущее состояние

- Source baseline TrafficHub обновлён 2026-10-01: `sergkuz219034-boop/TrafficHub/main` = `1b7a2dbb`.
- В source подтверждены HH employer OAuth, owner-scoped callback context, ручной обмен authorization code, импорт HH-ответов с job progress, runtime build trigger и защита oversized negotiation identifiers.
- Source baseline не равен production runtime: deploy подтверждается только `.deploy_commit`, health и release-проверками.

- `baza` остаётся Obsidian-vault, а не source repo приложения;
- live `TrafficHub` repo по read-only проверке `2026-07-18`:
  - `HEAD = 17bb3167f33d5314daa227a4ad0f49b00d462506`
  - worktree **не clean**: 30 modified и 8 untracked файлов;
  - app/worker runtime image marker: `75bb44c9fd2b324b57683b7f65537baa743458e1`;
  - точный source/runtime parity не подтверждён, см. [[03_Ошибки/Расследования/2026-07-18 полный аудит TrafficHub]].
- host contour вокруг `TrafficHub` уже вычищен от `freellmapi`, `hermes-webui`, `searxng-local`, `amnezia-xray` и `TrafficHub_backup_archive`.
- product contour на live healthy: `autolead_server_bot`, `traffichub_worker`, `traffichub_postgres`, `traffichub_redis`, `traffichub_account_manager`, `traffichub_license_*`, `traffichub_caddy`, `mfo_api`.
- active Autolead runtime migration по live-коду уже ушла дальше первых четырёх шагов:
  - PostgreSQL backend включён для `logs`, `delivery`, `leads`, `autofit`, `invites`, `control_sync`;
  - `docker-compose.yml` по умолчанию держит:
    - `AUTOLEAD_RUNTIME_LOGS_BACKEND=postgres`
    - `AUTOLEAD_RUNTIME_DELIVERY_BACKEND=postgres`
    - `AUTOLEAD_RUNTIME_LEADS_BACKEND=postgres`
    - `AUTOLEAD_RUNTIME_AUTOFIT_BACKEND=postgres`
    - `AUTOLEAD_RUNTIME_INVITES_BACKEND=postgres`
    - `AUTOLEAD_RUNTIME_CONTROL_SYNC_BACKEND=postgres`

## Что в фокусе

- стабилизировать новый канонический wiki-layer;
- держать архитектуру и runtime-слой синхронизированными с live;
- фиксировать баги и расследования через [[03_Ошибки/Отладка/Рецепт отладки|единый recipe]].
- отделить remaining SQLite fallback/test compatibility от реально active runtime path.

## Фактический этап миграции

- структурная миграция wiki в схему `00_Главное ... 04_План` фактически завершена;
- основной active runtime Autolead уже PostgreSQL-first;
- `traffic_hub` product DB на live тоже уже PostgreSQL-first;
- `control_store` на live тоже уже PostgreSQL-first, хотя `control.db` как legacy artefact всё ещё существует;
- SQLite остаётся в коде как fallback / compatibility / test surface, а не как основной live backend;
- следующий инженерный этап уже не “перенести `autofit`/`invites`/`control_sync`”, а:
  - проверить и сузить remaining SQLite surface;
  - решить, что оставлять как compatibility layer, а что можно удалить из active runtime contract.
- следующий wiki-этап:
  - синхронно поддерживать канон с кодом и runtime;
  - переводить новые расследования в [[03_Ошибки/Отладка/Рецепт отладки|контур отладки]] и подтверждённые знания в профильные разделы.
- сводная backend-матрица и ссылки на все подтверждения: [[00_Главное/Главная/Дашборд|Дашборд]]

## Roadmap по знаниям

- [[04_План/Разработка/Технический долг|Технический долг]]
- [[04_План/Разработка/Идеи и улучшения|Идеи и улучшения]]
- [[04_План/Разработка/Рефакторинг|Рефакторинг]]
- [[04_План/Разработка/Эксперименты|Эксперименты]]
