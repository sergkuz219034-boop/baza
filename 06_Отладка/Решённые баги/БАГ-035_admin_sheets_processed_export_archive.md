# БАГ-035: admin Sheets export не заполнял архив закрытых строк

## Симптом

- У `admin` основная Google Sheets таблица содержала тысячи строк со статусами `Нет номера`, `Нет оффера`, `Суточный лимит`, но отработанная таблица почти не росла.
- Пользовательский симптом: "не заполняется отработанная таблица на экспорт".

## Зона системы

- `modules/sheets_sync.py`
- `services/leads_service.py::run_full_cycle()`
- Google Sheets admin:
  - основная: `RabotaRu_Leads_Pending`
  - отработанная: `RabotaRu_Leads_Export`

## Гипотеза

- Export заполняется только для успешных terminal-результатов, а большинство закрытых строк остаётся только в основной таблице со статусом.

## Проверка

- Runtime под `bind_current_username("admin")`.
- До чистки в основной таблице было 18398 рабочих строк, из них 18321 строка с непустым `Статус`.
- Основные статусы закрытых строк:
  - `Нет номера`: 8390
  - `Нет оффера`: 4961
  - `Суточный лимит`: 3523
  - `Отправлено`: 555
  - `Дубль`: 342
- Код до фикса:
  - `append_processed_leads()` фильтровал только `is_campaign_result_processed()`;
  - `is_campaign_result_processed()` принимал только `sent`, `duplicate`, `already_sent`, `invited`, `already_invited`, `offer_disabled`;
  - `no_phone`, `no_offer`, `daily_limit`, `error` только помечались в основной таблице через `mark_pending_leads_processed()`.

## Наблюдение

- Отработанная таблица имела старый короткий header без `Резюме`, `Статус`, `Дата отработки`, `Офферы`.
- Дополнительный дефект: `get_processed_contact_keys()` при чтении отработанной таблицы вызывал `_ensure_headers(..., settings.EXPORT_FIELDS)` и мог снова портить header export.

## Вывод

- Google Sheets API работал корректно; причина была в контракте TrafficHub.
- Отработанная таблица фактически была "успешно обработанные", а не "все закрытые/отработанные".
- Для операционной очереди корректнее: основная таблица хранит только blank-status очередь, отработанная таблица хранит все закрытые результаты с причиной закрытия.

## Исправление

- Product commits:
  - `0e40d05c2` — `append_processed_leads()` архивирует все markable результаты и пишет полный export header.
  - `7e94da15f` — `get_processed_contact_keys()` использует тот же полный export header и больше не портит первую строку.
- Тесты:
  - `tests/test_sheets_queues.py`
  - `tests/test_leads_service_sheets_flow.py`
- Live deploy: `autolead_bot` и `worker` пересобраны и healthy.
- GitHub checks для `7e94da15f`: CI success, Docker build success.

## Чистка admin Google Sheets

- Перед чисткой включался maintenance mode для `admin`; после проверки выключен.
- Worker останавливался на время массовой перестройки строк.
- Backup до изменения:
  - container: `/app/data/runtime/backups/admin_sheets_cleanup_apply_20260630_215718`
  - host copy: `/home/codex/traffichub_runtime_backups/admin_sheets_cleanup_apply_20260630_215718`
- После чистки:
  - основная таблица: 70 строк, все со blank `Статус`;
  - `load_pending_leads_for_send()`: 70 строк;
  - отработанная таблица: 12569 строк;
  - processed contact keys: 18260;
  - обе таблицы имеют единый header:
    `Фио`, `Пол`, `Вакансия`, `Дата`, `Номер`, `Почта`, `Резюме`, `Город`, `Возраст`, `ДатаРождения`, `Статус`, `Дата отработки`, `Офферы`.

## Следующий шаг

- Не удалять backup до следующего успешного полного цикла admin.
- После следующего полного цикла проверить, что строка лога `Отработанная таблица: +N` появляется для закрытых `no_phone/no_offer/daily_limit` результатов, а основная таблица остаётся только рабочей очередью.
