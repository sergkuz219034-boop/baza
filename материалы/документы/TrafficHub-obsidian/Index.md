# TrafficHub / TrafServer — инженерная wiki

## Статус

- Канон: код, runtime, контейнеры, БД, env, логи и серверные артефакты.
- Эта wiki синхронизируется по двум классам источников:
  - live/server snapshot из `/root/TrafficHub`;
  - локальный evidence bundle: `artifacts/remote_edit/*`, `artifacts/remote_sync/docker-compose.yml`, `wiki/server-snapshot.md`, `wiki/server-control-manifest.md`.
- Локальный workspace не содержит полный checkout `TrafficHub`; подробности: [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-11 Локальный evidence bundle и границы канона]].
- На `2026-06-11` выполнен live SSH sync с `/root/TrafficHub`; актуальные факты вынесены в [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-11 Live server sync и расхождения compose-access]].
- На `2026-06-14` подтверждены крупные runtime-изменения worker:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Worker переведён на subprocess-per-owner и разрешил multi-owner parallel]]
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Worker serializes all owners while one job is active]] теперь historical context, а не текущий канон.
- На `2026-06-14` отдельно подтверждена нестабильность SSH transport до host:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Intermittent SSH instability to host 150.241.70.31]]
- На `2026-06-16` подтверждён канонический split SSH path между human session и Codex sandbox:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-16 Канонический SSH path для Windows ACL и Codex sandbox]]
- На `2026-06-16` внешний sync с GitHub-репозиторием `baza` восстановлен:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-16 Внешний sync с GitHub репозиторием baza восстановлен]]
- На `2026-06-16` отдельно подтверждено, что `baza` является внешней knowledge base под Obsidian, а не mutable code repo `TrafficHub`:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-16 Аудит репозитория baza как внешней knowledge base]]
- На `2026-06-14` `Воксис/leadsu` подтверждён не только blank DOM, но и ложный `submit not found` на непустом DOM:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Leadsu false submit not found on non-blank Voxys DOM]]
- На `2026-06-14` подтвержден отдельный UI/runtime mismatch heartbeat-логов:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Heartbeat статус задачи мигал как transient spinner]]
  - итоговый канон того же дня: heartbeat не копится в `app_log`, а рисуется на frontend как одна живая owner-scoped строка.
- На `2026-06-14` отдельно подтверждён frontend-bug, который затирал `ts` у уже структурированных log payload:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Frontend затирал ts у структурированных log messages]]
- На `2026-06-14` stop-path уточнён и починен:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Stop request lag и stop-сигнал без ⛔]]
- На `2026-06-14` debug HTML дал точную первопричину части offer-fill ошибок:
  - [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Debug HTML показал maxlength в Voxys и хрупкий submit-path Tilda]]
- Старые разделы `01-Architecture`, `02-Modules`, `03-API`, `04-Database`, `05-Configuration`, `06-Deployment`, `07-Testing`, `08-DevLog` считать legacy-слоем.
- Legacy-слой местами устарел:
  - локально в `[[материалы/документы/TrafficHub-obsidian/01-Architecture/Overview]]` система описана как один Python-процесс и три SQLite БД;
  - часть local bundle уже устарела относительно live compose на сервере;
  - live health на `2026-06-11` подтверждает `control.backend=postgres` и `legacy_import_enabled=false`.

## Быстрый вход

- За 5 минут: [[материалы/документы/TrafficHub-obsidian/02 Архитектура/00 Обзор]]
- Граница локального канона: [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-11 Локальный evidence bundle и границы канона]]
- Последняя live синхронизация: [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-11 Live server sync и расхождения compose-access]]
- Последний крупный runtime change: [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Worker переведён на subprocess-per-owner и разрешил multi-owner parallel]]
- Где искать текущую поломку: [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-07 Ничего не работает]]
- Как дебажить jobs и worker: [[материалы/документы/TrafficHub-obsidian/03 Плейбуки/Jobs и Worker]]
- Что хранится в state и БД: [[материалы/документы/TrafficHub-obsidian/04 Сущности/Job Queue]], [[материалы/документы/TrafficHub-obsidian/04 Сущности/Control Store]], [[материалы/документы/TrafficHub-obsidian/04 Сущности/Контейнеры и сервисы]]
- Как устроен доступ: [[материалы/документы/TrafficHub-obsidian/04 Сущности/Auth и Access]]
- Подтверждённые решения: [[материалы/документы/TrafficHub-obsidian/05 Решения/PostgreSQL control store]], [[материалы/документы/TrafficHub-obsidian/05 Решения/Очередь задач через Redis и worker]]

## Разделы

- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-11 Локальный evidence bundle и границы канона]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-11 Live server sync и расхождения compose-access]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Worker переведён на subprocess-per-owner и разрешил multi-owner parallel]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Intermittent SSH instability to host 150.241.70.31]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-16 Канонический SSH path для Windows ACL и Codex sandbox]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-16 Внешний sync с GitHub репозиторием baza восстановлен]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-16 Аудит репозитория baza как внешней knowledge base]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Leadsu false submit not found on non-blank Voxys DOM]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Heartbeat статус задачи мигал как transient spinner]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Frontend затирал ts у структурированных log messages]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Stop request lag и stop-сигнал без ⛔]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-14 Debug HTML показал maxlength в Voxys и хрупкий submit-path Tilda]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Platform fallback, disabled offer status и live debug прогон офферов]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Первый decomposition step api.server на dashboard_log_history]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Второй decomposition step api.server на dashboard_assets]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Третий decomposition step api.server на session_support]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Четвертый decomposition step api.server на account_manager_bridge и cleanup dead proxy path]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Первый decomposition step api.routers.settings на settings_bundle]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Второй decomposition step api.routers.settings на settings_rabota]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Третий decomposition step api.routers.settings на settings_sheets]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Четвертый decomposition step api.routers.settings на settings_maintenance]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Пятый decomposition step api.routers.settings на settings_core]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-15 Шестой decomposition step api.routers.settings на settings_license_accounts]]
- [[материалы/документы/TrafficHub-obsidian/01 Расследования/2026-06-07 Ничего не работает]]
- [[материалы/документы/TrafficHub-obsidian/02 Архитектура/00 Обзор]]
- [[материалы/документы/TrafficHub-obsidian/03 Плейбуки/Jobs и Worker]]
- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Auth и Access]]
- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Контейнеры и сервисы]]
- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Control Store]]
- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Job Queue]]
- [[материалы/документы/TrafficHub-obsidian/05 Решения/PostgreSQL control store]]
- [[материалы/документы/TrafficHub-obsidian/05 Решения/Очередь задач через Redis и worker]]
- [[материалы/документы/TrafficHub-obsidian/05 Решения/Autolead user settings и ownership]]

## Что известно как устаревшее

- `[[материалы/документы/TrafficHub-obsidian/01-Architecture/Overview]]` описывает `control.db` как основной источник пользователей и конфигурации.
  - Live compose на `2026-06-11` подтверждает `DATABASE_URL=postgresql+asyncpg://...`, `CONTROL_DB_PATH=/app/data/runtime/control.db`, `CONTROL_PG_LEGACY_IMPORT=false`.
- Часть старых описаний всё ещё говорит об отдельной SPA `/traffic/`.
  - Live `api/server.py` уже редиректит `/traffic` и `/traffic/{path}` обратно в основной dashboard; standalone SPA-модель устарела.
- `[[материалы/документы/TrafficHub-obsidian/01-Architecture/Overview]]` и часть server wiki описывают систему как `one process`.
  - Live compose и `docker ps` подтверждают отдельный контейнер `traffichub_worker`, работающий через Redis queue.

## Правило обновления

- Каждое расследование оформлять отдельной страницей в `01 Расследования`.
- Подтверждённые архитектурные факты переносить в `02 Архитектура`, `04 Сущности`, `05 Решения`.
- Если найдено расхождение между legacy-doc и кодом/runtime, указывать это явно на новой странице.
