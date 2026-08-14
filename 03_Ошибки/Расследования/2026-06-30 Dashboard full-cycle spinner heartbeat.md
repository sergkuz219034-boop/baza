# 2026-06-30 Dashboard full-cycle spinner heartbeat

## Симптом

Пользователь сообщил, что строка `Полный цикл выполняется` в dashboard по-прежнему визуально мигает после предыдущего фикса.

## Зона системы

- `dashboard/app.js`
- `tests/test_dashboard_realtime_spinner.py`
- websocket status heartbeat: `api/server.py::_push_status_loop`
- live container: `traffichub_app`

## Гипотеза

Предыдущий фикс убрал пересоздание `.log-spinner`, но строка всё ещё перезаписывалась на каждом status heartbeat из-за изменения duration/timestamp слева.

## Проверка

- В live repo `/root/TrafficHub` и контейнере `/app` подтверждено, что `syncRealtimeJobSpinner()` уже использует `updateRealtimeSpinnerLine()`, а не `appendLog()`.
- `api/server.py::_push_status_loop` шлёт status каждые 2 секунды.
- `dashboard/app.js::jobCycleDurationTimestamp()` пересчитывал `HH:MM:SS`, после чего `updateRealtimeSpinnerLine()` обновлял `.log-ts` даже при неизменных `status/command/job_id/msg`.
- Публичный `https://traffic-hub.pro/app.js` после deploy совпал по SHA-256 с `/app/dashboard/app.js`: `57fd3a861ce7e056819d0bb67e977196f6cae0bc7c37dc317907f9d673ae1b56`.

## Наблюдение

Мерцание было не backend-job и не повторным добавлением log-row. Остаточный визуальный эффект создавал frontend heartbeat-update: DOM-строка оставалась той же, но её timestamp/duration обновлялся без смыслового изменения статуса.

## Вывод

Канон для live spinner:

- `.log-spinner` создаётся один раз;
- повторный heartbeat с тем же `status/command/job_id/msg` не должен менять DOM;
- обновление допустимо только при смене статуса, команды, job id или текста progress.

Фикс product commit `50aa653da`: `dashboard/app.js` хранит `renderKey` в `line.dataset.renderKey` и не переписывает строку, если ключ не изменился. Regression guardrail добавлен в `tests/test_dashboard_realtime_spinner.py`.

Документационный commit `e55d4585e` обновил product `CHANGELOG.md`.

## Следующий шаг

Если пользователь всё ещё видит старое поведение, сначала проверить browser cache/service worker не требуется: asset отдаётся с `Cache-Control: no-cache, no-store` и новой query-version `app.js?v=1782802969`. Следующая проверка — открыть live dashboard в авторизованной Chrome-сессии и смотреть DOM mutation на `#realtime-job-spinner`.
