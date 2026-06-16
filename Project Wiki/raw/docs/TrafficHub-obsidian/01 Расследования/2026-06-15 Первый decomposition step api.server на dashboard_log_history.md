# 2026-06-15 Первый decomposition step `api.server` на `dashboard_log_history`

## Симптом

`api/server.py` оставался крупным hybrid-entrypoint, который одновременно держал:

- маршруты;
- auth/session;
- websocket;
- proxy/shell injection;
- helper-логику dashboard log history.

При этом log/history helper-блок был почти независим от роутинга и уже имел прямое тестовое покрытие.

## Зона системы

- `api/server.py`
- dashboard log feed
- history load из rotated/current log files

## Гипотеза

Первым безопасным шагом по разбору `api/server.py` можно вынести именно log/history helper-блок, не трогая HTTP маршруты.

## Проверка

На live source сервера:

- добавлен `api/dashboard_log_history.py`;
- `api/server.py` переведён на импорт:
  - `_load_log_history_messages`
  - `_normalize_dashboard_message`
  - `_is_dashboard_log_visible`
  - связанные regex/limit helpers

Проверки:

- `python3 -m compileall -q api/dashboard_log_history.py api/server.py ...`
- `docker exec autolead_server_bot python -m pytest -q tests/test_log_history.py -q`

## Наблюдение

- `compileall` прошёл.
- `tests/test_log_history.py` прошёл в runtime container с полным dependency stack.
- Системный `python3` на сервере по-прежнему не годится для API-тестов, поэтому каноничная проверка этого шага была сделана в контейнере.

## Вывод

Первый safe decomposition step для `api/server.py` подтверждён. Entry-point начал терять чистые helper-обязанности без изменения маршрутов.

## Следующий шаг

1. Выделить следующий helper-кластер из `api/server.py`:
   - auth/session helpers
   - account-manager proxy helpers
   - shell injection helpers
2. Продолжать проверять API-related decomposition через контейнерный test stack, а не через бедный системный `python3`.
