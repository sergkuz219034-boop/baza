## Симптом

- у пользователей периодически "слетают" Google Sheets настройки;
- export/import настроек опасен для multi-tenant контура;
- scheduler может считать пользователя активным для запуска даже без реального рабочего контура;
- runtime и compose содержат лишний сервисный слой, который усложняет дебаг и повышает drift.

## Зона системы

- `services/leads_service.py`
- `modules/sheets_sync.py`
- `api/routers/settings.py`
- `api/routers/settings_bundle.py`
- `tests/test_scheduler_config.py`
- `tests/test_sheets_queues.py`
- `docker-compose.yml`

## Гипотеза

- часть багов закреплена не случайным runtime-состоянием, а самим кодом нормализации и тестами;
- settings export/import работает как shared-global механизм, а не как owner-scoped операция;
- scheduler использует слишком слабый критерий "есть рабочий контур".

## Проверка

- live repo: `/root/TrafficHub`, HEAD `63ca3bb99`, host user `codex`;
- просмотрены `services/leads_service.py`, `modules/sheets_sync.py`, `api/routers/settings.py`, `api/routers/settings_bundle.py`, `docker-compose.yml`;
- подтверждено live runtime: `docker compose ps` содержит `traffichub_standalone_content_bot`;
- просмотрены и сопоставлены тесты `tests/test_scheduler_config.py`, `tests/test_settings_import_export.py`, `tests/test_sheets_queues.py`.

## Наблюдение

### 1. Google Sheets queue names принудительно затираются

- `services/leads_service.py:799-801` всегда выставляет:
  - `pending_sheet_name = "Все лиды"`
  - `processed_sheet_name = "Все лиды"`
- `modules/sheets_sync.py:19-20` держит те же жёсткие константы.
- `modules/sheets_sync.py:112-117` игнорирует входной конфиг и всегда возвращает константы.
- `tests/test_sheets_queues.py:98-106` закрепляет это поведение как ожидаемое.

Следствие:

- UI может показывать/сохранять одно, а runtime всё равно будет работать по жёстко вшитым именам;
- processed/pending контур фактически склеен на уровне worksheet-name.

### 2. Scheduler считает "google_sheets.enabled=true" достаточным признаком рабочего runtime

- `services/leads_service.py:960-971` возвращает `True`, если включён только `google_sheets.enabled`;
- `services/leads_service.py:776-788` по умолчанию выставляет `google_sheets.enabled = true`, если ключ отсутствует;
- `tests/test_scheduler_config.py:55-60` и `63-86` закрепляют это как валидное поведение.

Следствие:

- пользователь с неполным или пустым рабочим контуром может считаться schedulable;
- scheduler может запускать owner'ов, у которых нет реального источника данных/рассылки, а есть только default-конфиг.

### 3. Export/import настроек не изолирован по owner и может утянуть/стереть чужие secrets

- `api/routers/settings.py:401-403` экспортирует bundle без `bind_current_username(...)`;
- `api/routers/settings_bundle.py:22-30` считает exportable вообще все файлы из общего `secrets/`;
- `api/routers/settings_bundle.py:43-50` кладёт их в один bundle;
- `api/routers/settings_bundle.py:99-115` при import удаляет все существующие secrets, которых нет во входном архиве.

Следствие:

- operator/admin export получает shared secret-snapshot, а не безопасный owner-scoped export;
- import одного архива способен снести чужие service-account или auth-файлы, если они не вошли в payload.

### 4. Live runtime остаётся зашумлённым дополнительным сервисом

- `docker-compose.yml:280-300` содержит `standalone_content_bot`;
- live `docker compose ps` подтверждает активный контейнер `traffichub_standalone_content_bot`;
- одновременно `git status -sb` в `/root/TrafficHub` грязный по `AccountManager/*`, `docker-compose.yml` и untracked `standalone_content_bot/`.

Следствие:

- live-контур сложнее читать и воспроизводить;
- повышается риск drift между тем, что считается "основным продуктом", и тем, что реально работает на сервере.

## Вывод

- проблема "слетающих" таблиц и странного scheduler-поведения не локальна и не user-specific;
- как минимум две регрессии закреплены самим кодом и тестами;
- settings export/import сейчас архитектурно небезопасен для multi-tenant системы;
- live runtime нуждается в дальнейшей канонизации, иначе дебаг будет постоянно упираться в drift.

## Следующий шаг

1. Исправить `google_sheets` нормализацию: убрать принудительную перезапись `pending_sheet_name/processed_sheet_name`.
2. Развести queue worksheet semantics: `pending` и `processed` должны быть независимыми и документированными.
3. Ужесточить `_scheduler_run_enabled()`:
   - не считать default `google_sheets.enabled=true` достаточным;
   - требовать реальный runtime-path: offers, invite/responses/autofit или валидный queue-binding.
4. Переделать settings export/import в owner-scoped механизм:
   - export только в контексте текущего пользователя;
   - import без удаления чужих shared-secret файлов;
   - отдельный admin-only global backup делать явным отдельным endpoint.
5. Добить live cleanup:
   - убрать или вынести `standalone_content_bot` из основного compose-контура;
   - вернуть clean server repo перед следующими крупными изменениями.
