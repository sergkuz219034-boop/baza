# 2026-06-16 Worker image drift и queue workbook fallback в legacy spreadsheet

## Симптом

- live `admin/run` продолжал падать на старых ошибках `Ozon` и `Онекта`, хотя отдельный smoke в `autolead_server_bot` уже показывал более новый runtime-contract;
- пользователь ранее отдельно зафиксировал инвариант:
  - если `pending` или `processed` workbook не настроен, код не должен молча использовать основной `google_sheets.spreadsheet_id`.

## Зона системы

- runtime containers:
  - `autolead_server_bot`
  - `traffichub_worker`
- `modules/vbiv_bot.py`
- `modules/sheets_sync.py`
- `tests/test_sheets_queues.py`

## Гипотеза

1. `autolead_server_bot` и `traffichub_worker` работают на разных image/version, поэтому ручной smoke и реальный `run` исполняют разный код.
2. Queue-path для Google Sheets всё ещё содержит legacy fallback:
   - `pending_spreadsheet_id -> spreadsheet_id`
   - `processed_spreadsheet_id -> spreadsheet_id`
   что нарушает требование user-specific queue workbook binding.

## Проверка

1. Снят live-срез `admin`:
   - `job_status.status=running`
   - `last logs` содержали:
     - `Ошибка Ozon ... net::ERR_TIMED_OUT at https://tracking.lovko.pro/click?pid=4144&offer_id=22`
     - `Ошибка Онекта ... tilda: форма не подтверждена после отправки`
   - `admin` использует:
     - `pending_spreadsheet_id=1seCE2MPKZV01LJMvL4CuvSDL7IdG-V_vN6hmqoAcZOs`
     - `processed_spreadsheet_id=1vu2zNVWqMAl_jU3gs8AgCeDTxIFhvXHt1U5tHLID4m8`
   - вкладка вакансий на тот момент показывала:
     - `invite_available=124`
     - `invite_recommended=5`
     - `responses=586`
     - `invites=459`
2. Сравнение live-кода внутри контейнеров подтвердило drift:
   - в `autolead_server_bot` в `modules/vbiv_bot.py` уже был новый path:
     - `_should_use_form_proxy(...)`
     - `browser = _launch_browser(use_proxy=use_form_proxy)`
   - в `traffichub_worker` всё ещё жил старый path без этого helper.
3. `Playwright` smoke по `admin/Ozon` ссылке `pid=4144` подтвердил:
   - `direct` -> `Page.goto: net::ERR_TIMED_OUT`
   - `proxy` -> успешный переход на `https://vakansii-ozon.ru/...` с валидным HTML.
4. В `modules/sheets_sync.py` до правки подтверждено:
   - `_sheet_role_config()` fallback-ился на legacy `spreadsheet_id/spreadsheet_name`;
   - `get_processed_contact_keys()`, `load_pending_leads_for_send()`, `append_processed_leads()`, `mark_pending_leads_processed()` тоже fallback-ились на общий workbook.
5. Выполнены server-side действия:
   - `docker compose build worker && docker compose up -d worker`
   - затем `docker compose build autolead_bot worker && docker compose up -d autolead_bot worker`
   - после этого оба контейнера подтверждённо содержат один и тот же новый `vbiv_bot.py` path.
6. В `modules/sheets_sync.py` удалён queue fallback в legacy workbook:
   - `_sheet_role_config()` теперь возвращает только dedicated binding для `pending/processed`;
   - queue operations теперь заранее проверяют наличие queue workbook binding и не открывают общий `spreadsheet_id`.
7. Добавлены прямые тесты:
   - `test_sheet_role_config_does_not_fallback_to_legacy_spreadsheet_binding`
   - `test_load_pending_queue_does_not_fallback_to_legacy_spreadsheet`
   - `test_get_processed_contact_keys_does_not_fallback_to_legacy_spreadsheet`
8. Regression-check:
   - `docker exec -i autolead_server_bot python -m pytest -q tests/test_sheets_queues.py`
   - результат: `13 passed`.

## Наблюдение

- Прежний smoke в `autolead_server_bot` сам по себе не доказывал исправление `run/full cycle`, потому что реальное исполнение шло через отдельный `traffichub_worker`.
- Источник истины для runtime sender теперь нужно проверять в обоих контейнерах, если меняется код, участвующий в queue/worker path.
- User requirement по Google Sheets был реально нарушен кодом, а не только документацией:
  queue-path действительно мог свалиться обратно в основной workbook.

## Вывод

- На `2026-06-16` подтверждены два независимых runtime-дефекта:
  1. image drift между `autolead_server_bot` и `traffichub_worker`;
  2. legacy fallback queue workbook -> main workbook в `modules/sheets_sync.py`.
- Оба дефекта исправлены:
  - worker синхронизирован с актуальным image;
  - queue workbook больше не использует legacy `spreadsheet_id/spreadsheet_name` как silent fallback.

## Следующий шаг

1. Повторно проверить `admin/run` уже на синхронизированном worker-runtime.
2. Отдельно добить `Онекта/tilda` success-path и массовый `Ozon` path уже на новом worker image, если ошибки воспроизведутся снова.
3. Снять live-подтверждение, что `pending/processed` queue paths работают только через dedicated workbook bindings, а не через общий legacy workbook.
