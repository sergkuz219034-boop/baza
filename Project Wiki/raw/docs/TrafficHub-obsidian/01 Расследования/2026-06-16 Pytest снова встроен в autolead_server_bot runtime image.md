# 2026-06-16 Pytest снова встроен в `autolead_server_bot` runtime image

## Симптом

- В live runtime `autolead_server_bot` команда `python -m pytest ...` падала:
  - `/usr/local/bin/python: No module named pytest`
- Это противоречило части wiki, где уже встречалось утверждение, что `pytest` встроен в runtime image.

## Зона системы

- `requirements.txt`
- `Dockerfile`
- container `autolead_server_bot`
- wiki-страницы, ссылающиеся на `docker exec autolead_server_bot python -m pytest ...`

## Гипотеза

`pytest` был либо удалён из `requirements.txt`, либо текущий production image был пересобран из дерева, где этой зависимости уже не было, поэтому часть старой документации устарела.

## Проверка

1. Прочитан live `requirements.txt` на сервере:
   - `pytest` отсутствовал.
2. Проверен список модулей внутри `autolead_server_bot`:
   - `pytest False`
   - при этом `playwright`, `fastapi`, `gspread`, `psycopg`, `psycopg2` присутствовали.
3. В `requirements.txt` добавлен:
   - `pytest>=8.3.2`
4. Выполнен rebuild/restart `autolead_bot`.
5. После rebuild внутри нового container подтверждено:
   - `pytest True`
6. Затем прогнан релевантный regression-срез:
   - `tests/test_sheets_queues.py`
   - `tests/test_leads_service_sheets_flow.py`
   - `tests/test_jobs_router.py`
   - `tests/test_worker_parallel.py`
   - `tests/test_offers_import_export.py`
7. Итог test-run:
   - `33 passed, 2 warnings`

## Наблюдение

- На `2026-06-16` источник истины уже не совпадал с частью старой wiki:
  - документация местами считала `pytest` встроенным в runtime image;
  - живой контейнер это опровергал.
- После правки `requirements.txt` и rebuild runtime image снова пригоден для server-side regression smoke в том же контейнере, где крутится dashboard/API.

## Вывод

- Утверждение “`pytest` встроен в `autolead_server_bot`” было устаревшим до текущего rebuild.
- Новый подтверждённый канон с `2026-06-16`:
  - `pytest` снова входит в runtime image;
  - релевантные smoke/regression tests можно выполнять прямо внутри `autolead_server_bot`.

## Следующий шаг

1. При следующих rebuild не терять `pytest` из `requirements.txt`.
2. Если wiki ссылается на server-side `python -m pytest`, считать это валидным только после подтверждения внутри live container.
3. Отдельно синхронизировать страницы, где раньше это утверждалось без live-подтверждения.
