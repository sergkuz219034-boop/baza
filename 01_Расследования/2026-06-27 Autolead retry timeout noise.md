# 2026-06-27 Autolead retry timeout noise

## Симптом

- В live-логах `traffichub_worker` повторялись красные ошибки Autolead:
  - `Page.goto: net::ERR_TIMED_OUT` для `tracking.lovko.pro`;
  - `leadsu: форма не подтверждена после отправки`;
  - raw ответ Leads.su: `Internal server error: Timeout expired... server is not responding`.
- Ошибки проявлялись у нескольких owner, не только у `admin`: `admin`, `alex`, `artem`.

## Зона системы

- Autolead отправка офферов: `modules/vbiv_bot.py`.
- Leads.su recovery/direct submit: `modules/platforms/leadsu.py`.
- Retry queue: `services/leads_service.py`, `utils/runtime_store_pg_delivery.py`.
- Runtime таблица: `autolead_retry_queue`.

## Гипотеза

Внешние timeout партнёрок корректно попадают в retry, но слишком шумно повторяются: полный цикл может брать все просроченные retry-записи сразу. Для Leads.su raw timeout терялся и превращался в общее сообщение `форма не подтверждена`, из-за чего по логам было не видно реальную причину.

## Проверка

- Проверены контейнеры `traffichub_app`, `traffichub_worker`, `traffichub_caddy`, `traffichub_account_manager`.
- Проверен `/api/health` на `traffic-hub.pro` и `traffic-hubcrm.ru`.
- Проверена runtime таблица `autolead_retry_queue` по owner/offer/retry_count/next_retry_at.
- Проверены участки:
  - `services/leads_service.py::process_retry_queue`;
  - `modules/platforms/leadsu.py::_leadsu_submit_status_from_response`;
  - `modules/vbiv_bot.py::_is_permanent_form_failure`.

## Наблюдение

- Инфраструктурных падений после предыдущих фиксов нет: AccountManager scheduler и Hermes/Caddy не повторяют старые ошибки.
- Активные retry-записи были owner-scoped, но часть была просрочена и готова к повтору.
- `process_retry_queue()` выбирал все due-записи без лимита пачки.
- Leads.su raw timeout был внешней временной ошибкой партнёрки, но финальный текст становился слишком общим.

## Вывод

Причина текущего шума не в БД и не в изоляции пользователей. Это сочетание внешних timeout Lovko/Leads.su и слишком агрессивной обработки retry queue.

## Исправление

- `services/leads_service.py`: добавлен `retry_queue_batch_limit`, по умолчанию `3` записи за цикл.
- `modules/platforms/leadsu.py`: добавлено распознавание временного партнёрского timeout из raw direct-submit response.
- Добавлены тесты:
  - `tests/test_retry_queue_matching.py::test_process_retry_queue_limits_batch_size`;
  - `tests/test_vbiv_bot_runtime_errors.py::test_leadsu_partner_timeout_is_transient_reason`.

## Проверка после исправления

- `python -m pytest tests/test_retry_queue_matching.py tests/test_vbiv_bot_runtime_errors.py tests/test_leadsu_blank_recovery.py tests/test_leads_service_sheets_flow.py -q`
- Результат: `23 passed`.
- `docker compose up -d --build autolead_bot worker`.
- После стабилизации контейнеров свежие логи `traffichub_app`, `traffichub_worker`, `traffichub_caddy`, `traffichub_account_manager`, `traffichub_hermes` без новых `error/exception/timeout`.
- `/api/health` на `traffic-hub.pro` вернул `ok`.

## Следующий шаг

- Если timeout `tracking.lovko.pro` станет массовым, добавлять circuit breaker по partner URL: временно не пытаться отправлять все офферы этой партнёрки в текущем цикле, а переносить их в retry с cooldown.
