# PostgreSQL control store

## Проблема

Старая документация и часть legacy-кода описывали `control.db` и Google Sheets как основной источник пользователей и конфигурации.

## Контекст

- Live health на `2026-06-11` сообщает `control.backend=postgres` и `legacy_import_enabled=false`.
- Live compose задаёт:
  - `DATABASE_URL=postgresql+asyncpg://...`
  - `CONTROL_DB_PATH=/app/data/runtime/control.db`
  - `CONTROL_PG_LEGACY_IMPORT=false`
  - `CONTROL_LEGACY_SHEETS_FALLBACK=false`
  - `CONTROL_LEGACY_SHEETS_DUAL_WRITE=false`

## Решение

Считать PostgreSQL-backed control layer основным server source of truth для пользователей, ролей и control-path.

## Последствия

- расследования логина, ролей и ownership начинать с PostgreSQL/runtime, а не с legacy wiki;
- legacy `control.db` остаётся как migration/fallback artifact и требует осторожного обращения;
- документацию, где `control.db` назван primary source, считать устаревшей.

## Альтернативы

- Оставить `control.db` как primary source.
  - Отвергнуто runtime-фактами.
- Считать legacy полностью мёртвым.
  - Пока не доказано: env и часть кода всё ещё держат SQLite path как fallback.
