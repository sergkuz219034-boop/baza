# БАГ-040: остановленная рассылка оставалась `running`

Проверено: 2026-07-23.

## Симптом

После остановки ручной `send` job subprocess прекращался, но Redis state мог остаться `running`. UI блокировал следующий запуск, хотя worker не отправлял лиды.

## Причина

`job_stop_requested` сохраняется в persistent timeline до Redis pubsub. При потере обновления shared state worker не видел `stopping`; обычный cleanup не переводил job в terminal state.

## Фикс

`traffic_hub/worker.py::_reconcile_persisted_stop_requests()` читает последний persistent event для active job. При `job_stop_requested` завершает живой subprocess либо переводит orphaned job в `idle`, закрывает dangling run logs и сбрасывает stop flag.

Deploy: `49c49abb7`; health `GET /api/health` — `ok`.
