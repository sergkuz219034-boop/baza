# 2026-07-01 apply pending sheets and content bot changes

## Симптом

В `/root/TrafficHub` оставались незакоммиченные изменения:

- `modules/sheets_sync.py`
- `standalone_content_bot/app.py`
- `CHANGELOG.md`

Пользователь попросил применить их при необходимости.

## Зона системы

- Google Sheets export: `modules/sheets_sync.py`
- Content Bot runtime: `standalone_content_bot/app.py`
- тесты: `tests/test_sheets_queues.py`
- runtime-контейнеры: `traffichub_app`, `traffichub_worker`, `traffichub_standalone_content_bot`

## Гипотеза

Изменения полезны, но были недоведены:

- Sheets-блок менял формат отработанной таблицы на основные поля, но оставлял ссылку на удалённый `finished_at`;
- тесты всё ещё ожидали старую схему отработанной таблицы со статусными колонками;
- Content Bot-блок улучшал качество автопостов и снижал риск однотипных абстрактных текстов.

## Проверка

- `python3 -m py_compile modules/sheets_sync.py standalone_content_bot/app.py`
- targeted tests: `tests/test_sheets_queues.py`, `tests/test_leads_service_sheets_flow.py`, `tests/test_account_manager_content.py`
- full pytest: `431 passed, 43 skipped`
- live `/api/health`: `status=ok`
- runtime markers внутри `traffichub_app` и `traffichub_worker`:
  - `PROCESSED_EXPORT_FIELDS` содержит 10 основных колонок;
  - телефон экспортируется как текст `'+79991112233`.

## Наблюдение

Отработанная таблица теперь хранит только основные поля лида. Статусные поля остаются в основной pending-таблице как рабочий state для очереди.

Телефонные значения в Google Sheets записываются как текст с апострофом, чтобы Google Sheets не интерпретировал `+7...` как формулу.

Content Bot теперь:

- получает недавние опубликованные посты канала;
- просит LLM не повторять структуру и заголовки;
- отбрасывает generic-паттерны вроде `откройте двери`, `работа мечты`;
- имеет deterministic fallback под тему вакансий/работы.

## Вывод

Pending changes применены как product fix.

Product commit: `023bf20fb fix: apply sheets export and content bot cleanup`.

GitHub checks: `CI` и `Build and Push Docker Image` успешны.

## Следующий шаг

Если пользователю нужна история статусов именно во второй таблице, это надо вернуть отдельным осознанным решением, а не смешивать с `RabotaRu_Leads_Export` как основным clean export.
