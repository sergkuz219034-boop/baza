# 2026-07-01 Rabota response page progress old logs

## Симптом

В dashboard terminal снова появились старые строки процесса выгрузки Rabota.ru:

- `[i] Rabota.ru: начинаю загрузку откликов ...`
- `[i] Rabota.ru: отклики загружены: 100 (offset=0, страница=100)`
- `[OK] Уникальных откликов: 111 (из 111)`

Пользователь воспринимал это как возврат старого статуса выгрузки и лишнее мигание/шум в логах полного цикла.

## Зона системы

- `modules/rabota_api.py::RabotaRuClient.get_responses()`
- `utils/runtime_logging.py::is_ui_relevant_log()`
- `dashboard/app.js::isVisibleLogMessage()`
- `tests/test_runtime_logging.py`
- `tests/test_dashboard_realtime_spinner.py`
- live containers: `traffichub_app`, `traffichub_worker`

## Гипотеза

Старые строки вернулись не из-за rollback deploy, а потому что предыдущий фикс от 2026-06-30 сам добавил эти строки как "видимый business progress" и закрепил это тестом.

## Проверка

- Live product HEAD перед фиксом: `40716404c` после расследования.
- `modules/rabota_api.py::get_responses()` продолжал печатать постраничный progress через `_log_progress()`.
- `utils/runtime_logging.py` до фикса явно пропускал:
  - broad rule `msg.startswith('[i] Rabota.ru:')`;
  - substring `Уникальных откликов:`.
- Frontend `dashboard/app.js::isVisibleLogMessage()` не скрывал эти строки из уже сохранённой истории.
- Старый regression test `tests/test_runtime_logging.py::test_is_ui_relevant_log_keeps_rabota_business_progress` ожидал `True` для `Rabota.ru: отклики загружены`.

## Наблюдение

Это был не runtime rollback и не проблема websocket. Ошибка была в самом каноне логов: постраничный API progress оказался сделан пользовательским событием, хотя по смыслу это техническая telemetry долгого API-обхода.

## Вывод

Канон изменён: постраничные строки загрузки откликов Rabota.ru не должны попадать в dashboard terminal. В UI остаются фазовые бизнес-строки полного цикла и реальные ошибки; технический progress API должен оставаться невидимым для пользователя.

Product commit `40716404c Hide Rabota response page progress logs`:

- `utils/runtime_logging.py` отбрасывает `начинаю загрузку откликов`, `отклики загружены: N (offset=..., страница=...)`, `Уникальных откликов: ...`;
- удалён broad allow-list для всех `[i] Rabota.ru:`;
- `dashboard/app.js` скрывает эти строки и из исторических логов;
- tests обновлены: старый progress теперь должен быть `False`.

Live-проверка 2026-07-01:

- GitHub Actions `CI` и `Build and Push Docker Image` зелёные для `40716404c`;
- пересозданы `traffichub_app` и `traffichub_worker`;
- `/api/health` вернул `status=ok`;
- в live-контейнере `is_ui_relevant_log()` вернул `False` для трёх старых строк и `True` для `▶ Фаза 1: Сбор лидов с Rabota.ru` и ошибок.

## Следующий шаг

Если снова появляется "старый процесс" в dashboard logs, сначала проверить не только `runtime_logging.py`, но и frontend history-фильтр `dashboard/app.js::isVisibleLogMessage()`: сохранённые старые строки могут возвращаться из истории даже после backend-фильтра.
