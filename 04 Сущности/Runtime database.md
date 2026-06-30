# Runtime database

Теги: #сущность

## Тип

Таблица / модуль БД

## Где находится

`remote_server_snapshot/utils/database.py`

## Роль в системе

Хранит operational state Autolead runtime: owner-scoped `app_log`, кэш лидов, историю отправок, retry queue, run log и остальные runtime данные.

После commit `74ff3fd8d` дополнительно хранит persistent job timeline в таблице `autolead_job_events`. Эта таблица нужна, чтобы расследовать job после refresh/restart API, а не зависеть только от Redis/current-state.

## Invite history

`autolead_invite_history` — owner-scoped история Rabota.ru автоприглашений. Запись означает не только успешное новое приглашение, но и терминальное состояние `already_invited`, когда Rabota.ru ответила `RESPONSE_INVITE_REJECT_ERROR` для уже приглашённого или отклонённого кандидата.

Это важно для полного цикла: такие кандидаты должны уходить из очереди повторных попыток, иначе один и тот же ответ Rabota.ru будет повторяться в каждом запуске.

Кодовые точки:

- `modules/rabota_api.py::RabotaRuClient.invite_candidate`
- `modules/vbiv_bot.py::_try_auto_invite`
- `api/routers/offers.py::invite_bulk`
- `utils/runtime_store_pg_invites.py`

## Входы

- leads service
- settings cleanup endpoints

## Выходы

- runtime state
- статистика job-циклов
- persistent job timeline для `/api/jobs/timeline`

## Зависимости

- [[Leads service]]
- [[Multi-Tenant]]
- [[Job Timeline]]
- [[Runtime Inspector]]

## Типовые сбои или риски

- SQLite bottleneck;
- owner drift при ошибках в user context;
- destructive cleanup endpoints;
- очистка in-memory ленты без очистки persistent `app_log` даёт ложное ощущение успеха.
