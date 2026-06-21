# БАГ-003: live-проверка полного цикла admin

## Симптом

Полный цикл `admin` должен стабильно выполнять цепочку: выгрузка лидов, добавление строк в Google Sheets, обработка кандидатов по доступным офферам и фиксация итоговых статусов. После правки `БАГ-002` требовалась runtime-проверка на сервере.

## Зона системы

- `services/leads_service.py` — загрузка owner-scoped config, фазы `run_full_cycle`, `run_sender`.
- `modules/vbiv_bot.py` — matching кандидатов к `offer_mapping`, заполнение офферов, сбор `lead_results`.
- `modules/sheets_sync.py` — чтение основной таблицы, запись отработанной таблицы, отметка статусов в основной таблице.
- `utils/state.py` — Redis progress `traffic_hub:jobs:progress:<owner>`.
- PostgreSQL таблицы `autolead_send_history`, `autolead_retry_queue`, `autolead_run_log`.

## Гипотеза

Если live `admin` config действительно содержит 6 активных офферов, то код должен рассматривать все matching-офферы, а не только первый. Строки основной таблицы должны получать статус даже при ошибке внешней формы, дубле, лимите или отсутствии подходящего оффера.

## Проверка

- Серверная рабочая копия синхронизирована с GitHub `main` на commit `bd859c6`.
- Файлы `/app/modules/vbiv_bot.py` и `/app/modules/sheets_sync.py` в контейнерах `autolead_bot` и `worker` совпадают по SHA256 с GitHub-версией.
- Внутри live-контейнера прошли целевые тесты:
  - `tests/test_leads_service_sheets_flow.py`
  - `tests/test_sheets_queues.py`
  - `tests/test_vbiv_offer_matching.py`
- `services.leads_service.load_config(force_reload=True)` под `bind_current_username("admin")` возвращает 6 офферов:
  - `Дикси`
  - `Четыре лапы`
  - `ВкусВилл`
  - `X5`
  - `Воксис`
  - `Самокат`
- Read-only Sheets-проверка через `load_pending_leads_for_send()` подтвердила доступ к основной таблице: 435 неотработанных строк.
- Read-only `get_processed_contact_keys()` подтвердил доступ к отработанной таблице: 327 contact keys.
- Synthetic smoke на live `admin` config с замоканными Playwright/platform/history подтвердил matching всех 6 офферов:
  - vacancy `54258639` -> `Дикси`, `Четыре лапы`, `ВкусВилл`;
  - vacancy `54285960` -> `X5`, `Самокат`;
  - vacancy `54257329` -> `Воксис`.

## Наблюдение

Текущий live-run `admin` стартовал до гарантированного restart/reload сервисов. Он продолжает работать в `worker`, поэтому рестарт `autolead_bot` и `worker` во время проверки не выполнялся.

Фактический набор строк основной таблицы на момент проверки содержит первые строки с вакансией `Оператор чата поддержки`. Поэтому текущий live-run закономерно обрабатывает только matching-оффер `Воксис`, а не все 6 офферов. Это не противоречит логике matching: остальные офферы имеют другие `vacancy_id`.

В логах `worker` есть внешние ошибки `leadsu` для `Воксис`:

- `leadsu: форма не подтверждена после отправки`;
- `leadsu: кнопка submit не найдена`;
- связанные записи добавляются в `autolead_retry_queue`.

Debug artifacts `data/debug/debug_Воксис_20260617_164955.*` показали, что форма `#vacancy_form` и кнопка `#send_form` присутствуют, но на PNG перед ошибкой поля пустые и подсвечены validation-ошибками: фамилия, имя, возраст, телефон и checkbox не закрепились в DOM для jQuery validation.

Повторный live artifact `data/debug/debug_Воксис_20260618_181620.html/png` подтвердил тот же класс сбоя уже после сообщения `18:16:20 Ошибка Воксис [3]: leadsu: форма не подтверждена после отправки`:

- форма `#vacancy_form` валидируется через `jquery.validate`;
- submit handler отправляет `POST send2.php` через AJAX и открывает `#hidden-content` только при JSON `{"status":"success"}`;
- debug HTML после ошибки содержит `label.error` на `lname`, `fname`, `birthdate`, `phone`, `agree_accept`, а значения полей пустые;
- значит проблема не только в success selector, а в хрупкости UI-click/mask/validation слоя: runtime мог не получить подтверждение от `send2.php`, хотя DOM-форма и endpoint известны.

Правка в `modules/platforms/leadsu.py`:

- телефон приводится к маске `+7 (999) 123-45-67`;
- перед submit выполняется JS-стабилизация `lname`, `fname`, `phone`, `birthdate`, `service`, `city`, `agree_accept`;
- события `input/change/keyup/blur` диспатчатся и через DOM, и через jQuery, если он доступен;
- перед submit вызывается jQuery validation и логируется состояние формы.
- на commit `d7b11cf8` добавлен direct-submit recovery: если обычный UI-click не даёт popup/success, runtime повторно стабилизирует поля и отправляет тот же `FormData(#vacancy_form)` напрямую в `send2.php` с `X-Requested-With: XMLHttpRequest`;
- ответы `success` и `duplicate` от `send2.php` теперь считаются подтверждённым результатом, без зависимости от состояния popup после `form.reset()`;
- если после повторной стабилизации jQuery validation всё ещё возвращает `valid=false`, ошибка становится явной: `форма невалидна после повторного заполнения`, со state полей в логе.

Synthetic smoke через `run_campaign()` меняет Redis progress в `utils.state`. После проверки progress `admin` был восстановлен вручную до runtime-фактов: `sent=23`, `errors=46`, `total=418`.

После deploy `d7b11cf8` в контейнере `autolead_server_bot` прошли targeted tests:

- `tests/test_leadsu_blank_recovery.py`
- `tests/test_vbiv_offer_matching.py`
- `tests/test_retry_queue_matching.py`

Результат: `10 passed`.

## Вывод

Кодовая логика на commit `bd859c6` подтверждена тестами и synthetic smoke: все 6 офферов `admin` участвуют в matching и формируют `lead_results` с offer-status.

Live full-cycle ещё нельзя считать полностью доказанным без нового controlled run после deploy `d7b11cf8`. Текущий live-run покрывает только `Воксис`, потому что такие вакансии лежат в основной таблице. Ошибка `Воксис` имеет подтверждённую frontend-form/AJAX первопричину и закрыта кодовым recovery на уровне `send2.php`, но требует runtime-подтверждения на следующей реальной обработке Воксис.

## Следующий шаг

1. На следующей ошибке/успехе `Воксис` смотреть логи `leadsu: direct-submit response status=...`.
2. Если снова появится `форма не подтверждена`, проверять уже не только HTML/PNG, а raw response `send2.php` в логе recovery.
3. Запустить controlled smoke без записи в Sheets/БД или короткий live-cycle на ограниченном наборе строк, где представлены vacancy_id всех 6 офферов.
4. Проверить, что строки основной таблицы получают статусы `Отправлено`, `Дубль`, `Ошибка`, `Нет оффера` и что retry создаётся только для ошибочных внешних форм.
