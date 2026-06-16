# 2026-06-14 Frontend затирал ts у структурированных log messages

## Симптом

- Пользователь не видел время слева от строк в блоке `Логи работы`.
- При этом по backend/runtime уже было подтверждено, что heartbeat и обычные log messages сохраняются с `ts`.

## Зона системы

- Live code:
  - `/root/TrafficHub/dashboard/app.js`
  - `/root/TrafficHub/dashboard/style.css`
  - `/root/TrafficHub/api/server.py`
  - `/root/TrafficHub/utils/database.py`

## Гипотеза

- `ts` не терялся на сервере.
- Его затирал frontend при нормализации уже структурированных log payload.

## Проверка

- По live runtime подтверждено:
  - `api/server.py` и `utils.database.get_app_logs()` возвращают structured messages вида:
    - `{'ts': '2026-06-14 19:44:25', 'level': 'INFO', 'msg': '[i] Полный цикл: выполняется', 'spinner': 0}`
- В live `dashboard/app.js` подтверждён дефект:
  - `normalizeLogEntry(msg)` делал:
    - `parseHistoricalLogLine(msg.msg)`
    - затем `const merged = parsed ? { ...msg, ...parsed } : { ...(msg || {}) }`
  - для обычного structured payload `msg.msg` не содержал timestamp внутри строки;
  - `parseHistoricalLogLine()` возвращал:
    - `ts: ''`
    - `level: 'INFO'`
    - `msg: <тот же текст>`
  - это пустое `ts` затирало реальный `msg.ts`.
- Дополнительно найден слабый UI-фактор:
  - `.log-ts` была слишком бледной и без явного `display/min-width`, поэтому даже после исправления данных колонку времени лучше было усилить визуально.

## Наблюдение

- Это отдельный frontend-bug, не связанный с transient spinner heartbeat.
- Backend отдавал корректный `ts`, но structured payload проходил через historical parser, который нужен только для старых plain-text строк.

## Вывод

- На `2026-06-14` исправлено:
  - `dashboard/app.js`
    - structured payload больше не теряет `msg.ts`, если timestamp уже пришёл с сервера;
    - `compactLogTime()` больше не зависит от дефектного word-boundary regex и просто вытаскивает `HH:MM:SS`;
  - `dashboard/style.css`
    - `.log-ts` стала более контрастной и фиксированной по ширине.
- Hotfix залит в live container filesystem:
  - `autolead_server_bot:/app/dashboard/app.js`
  - `autolead_server_bot:/app/dashboard/style.css`

## Следующий шаг

- После обновления страницы пользователь должен увидеть слева timestamps `HH:MM:SS`.
- Если после hard refresh времени всё ещё не видно, следующий слой проверки уже только browser-side cache/session, а не server runtime.
