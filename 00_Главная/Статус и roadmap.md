# Статус и roadmap

## Текущее состояние

- `baza` остаётся Obsidian-vault, а не source repo приложения;
- live `TrafficHub` repo на `2026-06-16`:
  - `HEAD = a8f0be217fc7f23b8af6dead50b9968c9620cea1`
  - worktree clean
- host contour вокруг `TrafficHub` уже вычищен от `freellmapi`, `hermes-webui`, `searxng-local`, `amnezia-xray` и `TrafficHub_backup_archive`.
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
- фиксировать баги и расследования через [[06_Отладка/Рецепт отладки|единый recipe]].
- отделить remaining SQLite fallback/test compatibility от реально active runtime path.

## Фактический этап миграции

- основной active runtime Autolead уже PostgreSQL-first;
- SQLite остаётся в коде как:
  - fallback/test backend;
  - schema init для legacy-совместимости;
  - часть maintenance и локальных util-path;
- `control_store` при этом остаётся отдельным legacy/hybrid storage-контуром и не должен использоваться как shorthand-объяснение для всего runtime;
- следующий инженерный этап уже не “перенести `autofit`/`invites`/`control_sync`”, а:
  - проверить и сузить remaining SQLite surface;
  - решить, что оставлять как compatibility layer, а что можно удалить из active runtime contract.
- детальный live-аудит хвостов: [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-17 Remaining SQLite surface после PostgreSQL-first runtime]]

## Roadmap по знаниям

- [[07_Разработка/Технический долг|Технический долг]]
- [[07_Разработка/Идеи и улучшения|Идеи и улучшения]]
- [[07_Разработка/Рефакторинг|Рефакторинг]]
- [[07_Разработка/Эксперименты|Эксперименты]]
