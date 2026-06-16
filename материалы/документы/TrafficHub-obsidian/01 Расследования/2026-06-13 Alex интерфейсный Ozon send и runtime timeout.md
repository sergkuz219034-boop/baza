# 2026-06-13 Alex интерфейсный Ozon send и runtime timeout

## Симптом

- Требовалось не просто открыть Ozon/Lovko smoke-страницу вручную, а прогнать реальный пользовательский запуск `alex` через интерфейсный backend-путь и посмотреть owner-scoped live-log.
- При live `send` под `alex` Ozon дал:
  - `Ошибка Ozon [1]: Page.goto: net::ERR_TIMED_OUT at https://tracking.lovko.pro/click?pid=4126&offer_id=22`

## Зона системы

- Live server:
  - `/root/TrafficHub/traffic_hub/services/job_runner.py`
  - `/root/TrafficHub/utils/database.py`
  - `/root/TrafficHub/modules/vbiv_bot.py`
  - `/root/TrafficHub/api/server.py`
- Runtime data:
  - SQLite `leads`
  - SQLite `retry_queue`
  - owner-scoped `app_log`

## Гипотеза

- Ранее было подтверждено, что новый Lovko route `pid=4126` открывает Ozon-форму в ручном smoke через сервер.
- Нужно было проверить, совпадает ли это с реальным интерфейсным `send` у пользователя `alex`.
- Дополнительная гипотеза: кнопка `Рассылка` может идти не по тому же data-path, что `retry_queue`, и поэтому Ozon может не попадать в первые строки логов даже при наличии Ozon retry-записей.

## Проверка

- В live-коде подтверждено:
  - `POST /api/jobs/run` с `command="send"` вызывает `traffic_hub/services/job_runner.py`.
  - Для `send` job runner делает:
    - `load_config()`
    - `load_leads_for_send(days=3650)`
    - `leads_service.run_sender(config, leads)`
  - `send` не вызывает `process_retry_queue()`.
  - `process_retry_queue()` вызывается только в `run_full_cycle()` как фаза 4.
- Следствие:
  - попытки поднять Ozon через `retry_queue` не влияют на кнопку `Рассылка`;
  - Ozon для `send` нужно проверять через реальные записи `leads`, которые матчятся в `offer_mapping`.
- Live runtime-проверки для `alex`:
  - `pytest` встроен в runtime image и подтверждён внутри `autolead_server_bot`:
    - `pytest 8.4.2`
  - owner-scoped API под `alex` работал:
    - `GET /api/jobs/status`
    - `DELETE /api/logs`
    - `POST /api/jobs/run`
    - `GET /api/logs`
  - у `alex` найдены реальные Ozon-compatible leads с `vacancy_id`:
    - `54291412`
    - `54292479`
    - `54288634`
  - для целевого интерфейсного Ozon-прогона временно была поднята наверх одна реальная Ozon lead-запись `alex` через временную duplicate-row в `leads`;
  - после прогона временная строка удалена.
- Owner-scoped live-log `alex` за целевой запуск:
  - `2026-06-13 15:13:12 INFO: [i] Рассылка: в очереди`
  - `2026-06-13 15:13:12 INFO: [i] Рассылка: запущен`
  - `2026-06-13 15:13:13 INFO: [i] Рассылка: выполняется`
  - `2026-06-13 15:13:45 ERROR: Ошибка Ozon [1]: Page.goto: net::ERR_TIMED_OUT at https://tracking.lovko.pro/click?pid=4126&offer_id=22`

## Наблюдение

- Интерфейсный `send` для `alex` реально дошёл до Ozon, то есть:
  - матчинг по `offer_mapping` рабочий;
  - owner-scoped лог рабочий;
  - frontend/backend маршрут запуска рабочий.
- Но именно runtime path `send -> vbiv_bot -> Playwright page.goto()` всё ещё даёт timeout на Ozon/Lovko.
- Это расходится с ручным smoke, где та же ссылка ранее открывалась и форма находилась.
- Значит bug уже не в `retry_queue` и не в том, что “Ozon не выбирается”, а в различии между:
  - ручным smoke-контекстом;
  - реальным send-runtime контекстом внутри `vbiv_bot`.

## Вывод

- `pytest` теперь штатно установлен в production runtime image для `autolead_bot` и `worker`.
- Проверка “через интерфейс” для `alex` выполнена и подтверждает:
  - `send` действительно доходит до Ozon;
  - живой пользовательский лог это показывает;
  - текущая фактическая ошибка остаётся runtime timeout на `tracking.lovko.pro/click?pid=4126&offer_id=22`.
- Важный подтверждённый факт:
  - кнопка `Рассылка` не использует `retry_queue`;
  - `retry_queue` обрабатывается только в `Полный цикл`.
- После расследования в live server внесён runtime-fix:
  - `modules/vbiv_bot.py` делает retry открытия оффера (`lovko` до `3` попыток);
  - sender сокращает многострочную Playwright-ошибку до короткой строки;
  - `api/server.py` и `dashboard/app.js` дополнительно режут `Call log` в snapshot/UI.
- Повторный live smoke после фикса:
  - `alex/Ozon` открылся `5/5` раз;
  - один из пяти прогонов потребовал `2` попытки;
  - route не застревал в `about:blank` на финальном результате.

## Следующий шаг

- Если проблема повторится, проверять уже конкретно:
  - сколько попыток сделал retry-block;
  - был ли финальный URL отличным от `about:blank`;
  - не ушёл ли маршрут в `disabled`/anti-bot ветку.
- Отдельно прогонять `alex` через `Полный цикл`, если нужно проверить Ozon именно как часть `retry_queue`/phase 4, а не как обычный `send`.
