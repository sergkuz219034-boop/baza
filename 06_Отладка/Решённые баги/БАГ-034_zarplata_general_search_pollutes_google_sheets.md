# БАГ-034: Zarplata общий поиск загрязняет Google Sheets

## Симптом

- У `admin` полный цикл выглядит как "Google Sheets выгружается ненормально": основная таблица быстро растёт тысячами строк, а отработанная таблица может показывать `+0`.
- В worker log за 2026-06-30: Rabota добавила 31 строку, затем Zarplata добавила 2638 строк в основную Google Sheets таблицу.
- После рассылки лог показал: `основная таблица статусы обновлены 2687`, `отработанная таблица +0`.

## Зона системы

- `modules/zarplata_api.py`
- `modules/sheets_sync.py`
- owner-scoped config `zarplata_ru` и `google_sheets`
- Google Sheets admin:
  - основная: `RabotaRu_Leads_Pending`
  - отработанная: `RabotaRu_Leads_Export`

## Гипотеза

- Проблема не в доступе к Google Sheets, а в источнике данных Zarplata: импорт берёт слишком широкую выдачу резюме.

## Проверка

- Проверен runtime под `bind_current_username("admin")`.
- `google_sheets.enabled=True`; service account `/app/data/runtime/secrets/service_account__admin.json` существует.
- Sheets открываются по ID, worksheet `Все лиды` доступен.
- Worker log подтвердил успешную запись:
  - Rabota: `Google Sheets: добавлено 31 записей`.
  - Zarplata: `Google Sheets: добавлено 2638 записей`.
- Конфиг admin Zarplata:
  - `enabled=True`
  - `query=Оператор колл-центра`
  - `per_page=3`
  - `include_response_search=None`
  - `include_negotiations=None`
- Код до фикса в `modules/zarplata_api.py::import_resumes()` всегда сначала вызывал `search_all_resumes(... only_in_responses=False)`.

## Наблюдение

- Основная таблица содержит 19039 строк; основные статусы:
  - `Нет номера`: 8390
  - `Нет оффера`: 4961
  - `Суточный лимит`: 3523
- Неотработанных строк после статусов осталось 69.
- Отработанная таблица содержит 1035 строк; `+0` при полном цикле допустимо, если новые результаты не являются terminal processed или уже есть в processed contact set.

## Вывод

- Google Sheets у admin работает: чтение, запись и обновление статусов проходят.
- Ненормальный объём создавал не Sheets layer, а Zarplata importer: общий поиск по `Оператор колл-центра` попадал в основную таблицу вместе с откликами/negotiations.
- Старый default был опасным для live: отсутствие `include_general_search` трактовалось как "общий поиск включён".

## Исправление

- Product commit: `00f4e388b`.
- `modules/zarplata_api.py` теперь запускает общий поиск Zarplata только при явном `zarplata_ru.include_general_search=true`.
- Default для новых профилей: `include_general_search=False`.
- API settings allow-list принимает `zarplata_include_general_search`, чтобы режим можно было включить явно.
- Тесты `tests/test_zarplata_api.py` обновлены:
  - общий поиск проверяется только с явным `include_general_search=True`;
  - default path проверяет, что broad generic search не попадает в Sheets.

## Следующий шаг

- Если нужна чистка уже залитых строк, делать отдельной процедурой: фильтровать rows по источнику/дате/статусам и не удалять вручную без snapshot/export.
- Добавить UI-переключатель "Общий поиск Zarplata" только если пользователю реально нужен массовый sourcing, иначе держать режим скрытым и выключенным.
