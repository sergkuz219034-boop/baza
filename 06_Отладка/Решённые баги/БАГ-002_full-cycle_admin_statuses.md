# БАГ-002: full-cycle admin не фиксировал часть статусов

## Симптом

В полном цикле `admin` часть кандидатов могла оставаться в pending-таблице без статуса после обработки: ошибки офферов, отсутствие подходящего оффера, суточный лимит или временная недоступность не всегда доходили до `mark_pending_leads_processed`.

## Зона системы

- `services/leads_service.py` — `run_full_cycle`, `run_sender`.
- `modules/vbiv_bot.py` — `run_campaign`.
- `modules/sheets_sync.py` — `append_processed_leads`, `mark_pending_leads_processed`.
- `utils/database.py` / `utils/runtime_store_pg_delivery.py` — owner-scoped `send_history`.

## Гипотеза

После PostgreSQL-миграции история отправок хранится как `owner:phone:offer`, но `run_campaign` местами проверял ключ как `phone:offer`. Из-за этого уже обработанные офферы могли считаться новыми. Дополнительно `lead_results` возвращались только для `processed=True`, поэтому неуспешные, но фактически рассмотренные кандидаты не получали статус в pending.

## Проверка

- `utils.database._compose_history_key()` формирует ключ `owner:phone:offer`.
- `utils.runtime_store_pg_delivery.load_send_history()` возвращает `history_key` из PostgreSQL.
- `modules.vbiv_bot.run_campaign()` сравнивает историю через `utils.database._compose_history_key()`.
- `modules.sheets_sync.is_campaign_result_pending_markable()` принимает любой результат, где есть итоговый offer-status.
- Регрессия покрыта тестами `tests/test_vbiv_offer_matching.py`, `tests/test_sheets_queues.py`, `tests/test_leads_service_sheets_flow.py`.

## Наблюдение

Кандидат с ошибкой оффера попадал в `retry_queue`, но не всегда попадал в `lead_results`. Поэтому `run_full_cycle()` не мог передать его в `mark_pending_leads_processed()`. Для `admin` уже отправленный оффер мог повторно пройти в обработку, потому что ключ истории был несопоставим с PostgreSQL-форматом.

## Вывод

Канон full-cycle:

- каждый рассмотренный лид должен вернуть `lead_results`, если по нему есть итоговый статус;
- успешные/терминальные статусы идут в processed-таблицу;
- операторские статусы пишутся обратно в pending: `Ошибка`, `Нет оффера`, `Суточный лимит`, `Временно недоступен`, `Нет номера`, `Иностранный номер`, `Некорректный номер`, `Уже отправлено`, `Отправлено`, `Дубль`;
- история отправок сравнивается только через `utils.database._compose_history_key()`.

## Следующий шаг

Live-проверка вынесена в [[БАГ-003_live_admin_full_cycle_verification]]. На commit `bd859c6` подтверждены:

- owner-scoped `send_history`;
- markable pending-статусы для ошибок и skip-сценариев;
- matching всех 6 офферов `admin` на synthetic smoke с live config.

Остаётся дождаться завершения текущего live `admin` job и выполнить restart/reload сервисов перед финальной runtime-проверкой.
