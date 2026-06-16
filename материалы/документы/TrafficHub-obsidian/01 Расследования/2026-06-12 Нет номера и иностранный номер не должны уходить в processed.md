# 2026-06-12 Нет номера и иностранный номер не должны уходить в processed

## Симптом

- лиды без номера или с иностранным / некорректным номером должны получать статус;
- но такие лиды не должны попадать в `отработанную таблицу`.

## Зона системы

- `modules/vbiv_bot.py`
- `modules/sheets_sync.py`
- `services/leads_service.py`

## Гипотеза

- runtime уже умел ставить статус `Нет номера`, но считал такой результат `processed`;
- из-за этого `append_processed_leads()` добавлял такие строки в processed Google Sheet.

## Проверка

- подтверждено по коду:
  - `vbiv_bot.py` создавал `lead_result` со статусом `no_phone` и ставил `lead_result["processed"] = True`;
  - `modules/sheets_sync.py` включал `no_phone` в `_PROCESSED_TERMINAL_STATUSES`;
  - `append_processed_leads()` переносил все `r.get("processed")` в processed sheet.
- отдельный runtime-smoke после правки подтвердил контракт:
  - `no_phone`:
    - `processed=False`
    - `pending_markable=True`
    - `status_text='Нет номера'`
  - `foreign_phone`:
    - `processed=False`
    - `pending_markable=True`
    - `status_text='Иностранный номер'`
  - `invalid_phone`:
    - `processed=False`
    - `pending_markable=True`
    - `status_text='Некорректный номер'`

## Наблюдение

- теперь есть два разных класса terminal outcomes:
  - `processed`:
    - `sent`
    - `duplicate`
    - `already_sent`
    - `invited`
    - `already_invited`
  - `pending-only status`:
    - `no_phone`
    - `foreign_phone`
    - `invalid_phone`
- pending sheet может быть помечен статусом, даже если результат не идёт в processed sheet.

## Вывод

- корневая причина была в смешении двух понятий:
  - `результат надо пометить статусом`
  - `результат надо перенести в processed table`
- после правки они разведены:
  - skip по номеру получает статус в основной таблице;
  - в отработанную таблицу такой лид не переносится.

## Следующий шаг

- если потребуется, аналогично развести и другие skip-сценарии:
  - `нет оффера`
  - `ошибка`
  - `дневной лимит`

## См. также

- [[материалы/документы/TrafficHub-obsidian/04 Сущности/Google Sheets]]
- [[материалы/документы/TrafficHub-obsidian/03 Плейбуки/Jobs и Worker]]
