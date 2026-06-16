# 2026-06-12 Порядок дат в Google Sheets

## Симптом

- пользователь попросил проверить, что даты в основной и отработанной таблице идут по порядку у всех пользователей;
- на runtime это означало проверку листов `Все лиды` в `pending` и `processed` Google Sheets по колонке `Дата`.

## Зона системы

- `services/leads_service.py`
- `modules/sheets_sync.py`
- user-scoped `google_sheets` config из `load_config()`
- Google Sheets runtime через `gspread` и user-scoped service account

## Гипотеза

- часть таблиц уже была отсортирована по возрастанию `Дата`;
- `processed` лист мог ломать порядок после новых запусков, если runtime делает `append_rows()` в порядке завершения кампаний, а не выполняет post-append reorder;
- часть пользователей делит одни и те же spreadsheet ID, поэтому проверять нужно не только user-by-user, но и по уникальным sheet targets.

## Проверка

- через `bind_current_username(username) + load_config(force_reload=True)` сняты реальные user configs;
- первичный runtime-аудит 2026-06-12 действительно видел shared targets для `Artem`, `admin`, `debuglogs`;
- повторная проверка control store на 2026-06-12 после последующих чисток показала уже 4 активных пользователя:
  - `ARTEM2`
  - `Artem`
  - `admin`
  - `alex`
- подтверждены shared sheets:
  - `Artem`, `admin` используют одну и ту же `processed` таблицу `1vu2zNVWqMAl_jU3gs8AgCeDTxIFhvXHt1U5tHLID4m8`
- первичный аудит по колонке `Дата` показал нарушения:
  - `ARTEM2 processed` `10tCmh8ZFbHhmNohrZRNedfY81K2_olYJnjk623HRnMY`: `15` broken pairs
  - shared `pending` `1seCE2MPKZV01LJMvL4CuvSDL7IdG-V_vN6hmqoAcZOs`: `1` broken pair
  - shared `processed` `1vu2zNVWqMAl_jU3gs8AgCeDTxIFhvXHt1U5tHLID4m8`: `4` broken pairs
  - `alex processed` `1y5Va3ViWjqm-3eZivx84mULsmrdWbDQLVUOKLwkjB6g`: `1` broken pair
- перед правкой на сервере созданы backups:
  - `/app/data/backups/sheet_order_backup_processed_10tCmh8ZFbHhmNohrZRNedfY81K2_olYJnjk623HRnMY_20260612-161212.json`
  - `/app/data/backups/sheet_order_backup_pending_1seCE2MPKZV01LJMvL4CuvSDL7IdG-V_vN6hmqoAcZOs_20260612-161301.json`
  - `/app/data/backups/sheet_order_backup_processed_1vu2zNVWqMAl_jU3gs8AgCeDTxIFhvXHt1U5tHLID4m8_20260612-161303.json`
  - `/app/data/backups/sheet_order_backup_processed_1y5Va3ViWjqm-3eZivx84mULsmrdWbDQLVUOKLwkjB6g_20260612-161306.json`
- затем проблемные листы отсортированы по возрастанию `Дата` с сохранением header row.
- на момент 2026-06-12 первопричина повторного рассыпания порядка была подтверждена так:
  - `modules/sheets_sync.py -> append_processed_leads()`
  - runtime делал только `worksheet.append_rows(rows, value_input_option="RAW")`
  - после append не было никакой пересортировки `processed` листа.
- на тот момент в серверный runtime был добавлен временный инвариант:
  - helper `_sort_worksheet_by_date()`
  - вызов `_sort_worksheet_by_date(worksheet, "Дата")` сразу после `append_rows()` в `append_processed_leads()`.
- позже, 2026-06-15, этот путь был уточнён:
  - runtime перестал полагаться только на `append + full sort`;
  - вместо этого добавлен insertion-by-date path через `insert_rows`, см. отдельное расследование.
- после деплоя и пересборки контейнеров повторный server-side аудит/repair показал:
  - `owners=ARTEM2`: `before=0 -> after=0`
  - `owners=Artem`: `before=3 -> after=0`
  - `owners=admin`: `before=0 -> after=0`
  - `owners=alex`: `before=0 -> after=0`

## Наблюдение

- повторный аудит после сортировки показал `broken_pairs = 0` у всех пользователей и у обеих таблиц;
- проблема была не только в исторически кривых данных, но и в самом runtime-path записи `processed` таблицы;
- после временного server fix новые append в `processed` перестали оставлять строки в порядке завершения задач;
- более поздний runtime фикс 2026-06-15 заменил грубую post-append сортировку на insertion-by-date path;
- канонический порядок сейчас:
  - `pending`: по возрастанию `Дата`
  - `processed`: по возрастанию `Дата`
- shared sheet targets действительно влияют сразу на несколько пользователей:
  - правка одной общей таблицы исправляет сразу всех владельцев этого spreadsheet target.

## Вывод

- на 2026-06-12 порядок дат был нарушен не у всех, а в 4 уникальных sheet targets;
- историческая server-side сортировка устранила следствие, но не была финальной формой решения;
- подтверждённая первопричина на 2026-06-12: `append_processed_leads()` добавлял строки в `processed` через `append_rows()` без post-append reorder;
- на 2026-06-15 runtime переведён на insertion-by-date path, поэтому текущее каноническое решение уже другое;
- источник истины здесь не локальные настройки, а runtime-комбинация:
  - `load_config()` под нужным owner
  - `service_account_file`
  - реальные spreadsheet IDs в Google Sheets.

## Следующий шаг

- при следующем инциденте повторять audit не по username, а по уникальным `(service_account_file, spreadsheet_id, sheet_name, role)` targets;
- если появятся новые разрывы, проверять не только `processed`, но и любые внешние ручные вставки / правки самих Google Sheets.

## См. также

- [[04 Сущности/Google Sheets]]
- [[01 Расследования/2026-06-15 Google Sheets insertion-by-date вместо append в конец]]
- [[05 Решения/Autolead user settings и ownership]]
