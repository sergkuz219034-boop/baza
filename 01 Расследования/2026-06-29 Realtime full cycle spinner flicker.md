# 2026-06-29 Realtime full cycle spinner flicker

## Симптом

В UI строка realtime-статуса вида `Полный цикл: выполняется` мигала/дёргалась во время работы задачи.

## Зона системы

- `dashboard/app.js`
- websocket `/ws/status`
- fallback `refreshJobStatus()` polling

## Гипотеза

Проблема не в тексте строки, а в гонке между несколькими источниками статуса:

- websocket snapshot;
- HTTP refresh;
- локальный секундный ticker для elapsed-time.

Если один из промежуточных snapshot'ов на короткий момент отдаёт не `running`, spinner-строка удаляется и тут же рисуется заново.

## Проверка

1. Проверен live `dashboard/app.js`.
2. Подтверждено, что realtime-строка обновляется через `syncRealtimeJobSpinner(data)`.
3. До фикса логика сразу удаляла строку при любом статусе вне `queued/running`.
4. Добавлен grace-period удаления:
   - новый `realtimeSpinnerRemovalTimer`;
   - `stopping` считается активным transitional статусом;
   - удаление spinner-строки теперь откладывается на `2500 ms`;
   - если за это время приходит новый `queued/running/stopping`, удаление отменяется.
5. Обновлённый `dashboard/app.js` подложен в `traffichub_app`.
6. `api/health` внутри контейнера отвечает `ok`.

## Наблюдение

- В live-файле уже была более аккуратная реализация `updateRealtimeSpinnerLine()` без полного `innerHTML` repaint.
- Оставшийся дефект был именно в слишком агрессивном remove-path, а не в render-path.

## Вывод

Первопричина мигания — кратковременные статусные провалы между WS и HTTP snapshot'ами.

Исправление: spinner больше не исчезает мгновенно на промежуточном статусе и переживает короткие race-condition окна.

## Следующий шаг

- Проверить на реальном `Полный цикл`, что строка больше не мигает визуально.
- Если симптом повторится, следующая зона — серверный источник `/api/jobs/status` и порядок публикации событий в `ws/status`.
