# 2026-06-12 Пропущен один лид в pending Google Sheets

## Симптом

- в `RabotaRu_Leads_Pending` одна строка осталась без `Статус / Дата отработки / Офферы`, хотя соседние строки уже отработаны;
- пользователь указал на визуально одиночный пропуск среди уже размеченных лидов.

## Зона системы

- `modules/sheets_sync.py`
- `modules/vbiv_bot.py`
- `services/leads_service.py`
- shared pending workbook `RabotaRu_Leads_Pending`

## Гипотеза

- лид не теряется на чтении Google Sheets;
- лид не является processed-дублем;
- потеря происходит между формированием очереди отправки и записью `lead_results` обратно в pending sheet.

## Проверка

- runtime-проверка pending workbook для `admin` подтвердила проблемную строку:
  - row `100`
  - `Фио`: `Анастасия Голикова Андреевна`
  - `Номер`: `нету`
  - `Почта`: `golikovaanastagolikova@yandex.ru`
  - `Статус`: пусто
- соседние строки:
  - `99` уже имеют `Отправлено`
  - `103` уже имеют `Некорректный номер`
- runtime-проверка `load_pending_leads_for_send(config)` подтвердила:
  - лид с `Фио = Анастасия Голикова Андреевна`
  - `_sheet_row = 100`
  - попадает в очередь `pending_leads_for_send`
- значит строка:
  - не отсекается как пустая;
  - не исключается как already processed;
  - не ломается на чтении Google Sheets.
- server-side code path, подтверждённый ранее:
  - `run_full_cycle()` берёт `pending_leads = load_pending_leads_for_send(config)`
  - затем отправляет `all_leads_to_send` в sender / campaign
  - после этого только `send_stats["lead_results"]` попадают в `mark_pending_leads_processed(config, lead_results)`
- `mark_pending_leads_processed()` умеет писать статус даже для `no_phone`, если соответствующий `result` вообще присутствует в `lead_results`.

## Наблюдение

- проблема не в pending-sheet read path;
- проблема не в отображении статусов `Нет номера / Некорректный номер`;
- одиночный лид без номера остался без статуса, потому что не попал в тот `lead_results` батч, который потом ушёл в writeback.

## Вывод

- подтверждённая причина класса проблемы:
  - отдельные лиды могут оказаться в `pending_leads_for_send`, но не попасть в `lead_results` конкретного запуска;
  - в таком случае `mark_pending_leads_processed()` о них ничего не знает и не проставляет статус.
- для этого кейса наиболее вероятный runtime-сценарий:
  - batched / prioritized send прошёл не по линейному порядку строк;
  - лид без телефона не был обработан в том конкретном запуске, несмотря на то что соседние строки уже были размечены.

## Следующий шаг

- server fix:
  - добавить отдельный pre-writeback или pre-send pass, который гарантированно маркирует pending rows с `Номер = нету` статусом `Нет номера`, даже если основной send-batch не дошёл до них;
  - либо маркировать такие строки прямо в `load_pending_leads_for_send()` / отдельной preprocessing ветке до запуска campaign.
- operational check:
  - при следующем доступе к серверу дочитать полный runtime-path между `pending_leads_for_send` и `lead_results`, чтобы зафиксировать точную точку выпадения.
