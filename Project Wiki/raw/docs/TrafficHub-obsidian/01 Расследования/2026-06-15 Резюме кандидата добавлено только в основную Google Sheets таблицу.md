# Резюме кандидата добавлено только в основную Google Sheets таблицу

## Симптом

- пользователь не видел колонку `Резюме` в основной Google Sheets таблице;
- ссылки на резюме кандидатов не попадали в экспорт;
- было дополнительное требование: поле `Резюме` должно появляться только в основной таблице пользователя, а не в `processed`/отработанной.

## Зона системы

- `config/settings.py`
- `utils/data_processor.py`
- `modules/sheets_sync.py`
- runtime контейнеры:
  - `autolead_server_bot`
  - `traffichub_worker`

## Гипотеза

- колонка не появлялась, потому что канонический список экспортируемых полей не содержал `Резюме`;
- даже после добавления поля в экспорт его мог сломать жёстко зашитый диапазон заголовков `A1:I1`;
- shared `EXPORT_FIELDS` использовался и для основной, и для отработанной таблицы, поэтому прямое добавление `Резюме` туда нарушило бы инвариант “только основная таблица”.

## Проверка

- на live-сервере прочитан `config/settings.py`: подтверждено, что `settings.EXPORT_FIELDS` не содержал `Резюме`;
- на live-сервере прочитан `modules/sheets_sync.py`: подтверждено, что upload-path правил заголовки через фиксированный диапазон `A1:I1`;
- на live-сервере прочитан `utils/data_processor.py`: подтверждено, что `normalize_lead()` не формировал поле `Резюме`;
- отдельно подтверждено, что `append_processed_leads()` и `get_processed_contact_keys()` используют тот же список `settings.EXPORT_FIELDS`, то есть без разделения полей `Резюме` попало бы и в processed sheet.

## Наблюдение

- на сервере введено разделение:
  - `settings.EXPORT_FIELDS` — базовые поля без `Резюме` для processed sheet;
  - `settings.MAIN_EXPORT_FIELDS` — поля основной таблицы с колонкой `Резюме`;
- `normalize_lead()` теперь сохраняет `lead["Резюме"]`;
- если Rabota raw payload не содержит прямой URL, runtime строит fallback `https://www.rabota.ru/resume/{resume_id}`;
- `upload_to_sheets()` больше не обновляет заголовки жёстким диапазоном `A1:I1`, а использует динамический диапазон по длине headers;
- pending/main flows в `modules/sheets_sync.py` переведены на `settings.MAIN_EXPORT_FIELDS`;
- processed flows оставлены на `settings.EXPORT_FIELDS`;
- после rebuild выявился отдельный runtime-дефект: `api/server.py` использовал `threading.Event()` без `import threading`; дефект исправлен, `autolead_server_bot` снова healthy.

## Вывод

- причина была не в одной точке, а в трёх слоях сразу:
  - отсутствие поля в export contract;
  - отсутствие нормализации ссылки;
  - shared headers для main/processed;
- итоговый runtime contract:
  - `Резюме` есть только в основной таблице пользователя;
  - processed sheet остаётся без этой колонки;
  - заголовки main sheet теперь могут расширяться без регресса на фиксированный `A1:I1`.

## Следующий шаг

- сделать live-проверку на реальной пользовательской основной таблице через сохранённый `service_account_file` конкретного пользователя:
  - колонка `Резюме` реально создаётся;
  - ссылки сохраняются в новые строки;
  - processed sheet не получает новую колонку;
- после проверки синхронизировать `CHANGELOG.md`/server README в основном server checkout, если этого ещё нет.
