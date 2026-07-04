# 2026-07-04 admin full cycle Rabota/Zarplata realtime

## Симптом

Пользователь не видел понятный статус выгрузки Зарплата.ру в realtime-строке полного цикла. Также требовалось проверить, что полный цикл `admin` работает по строгому выбранному периоду и не забирает старую общую pending-очередь.

## Зона системы

- Live repo: `/root/TrafficHub`
- Worker/job queue: `traffic_hub/services/job_queue.py`, `traffic_hub/services/job_runner.py`, `traffic_hub/worker.py`
- Полный цикл: `services/leads_service.py`
- Зарплата.ру importer: `modules/zarplata_api.py`
- Realtime progress: `utils/state.py`, `dashboard/app.js`
- Google Sheets queue: `modules/sheets_sync.py`

## Гипотеза

1. Rabota.ru и Зарплата.ру реально выполняются, но Зарплата.ру пишет прогресс только в stdout/log, а не в `utils.state.progress`.
2. Общая pending-очередь из Google Sheets может обходить фильтр периода перед заполнением анкет.

## Проверка

Live job `admin` был поставлен в очередь как `run` с `period=30`.

Подтвержденные runtime-факты:
- Rabota.ru API запросил отклики за `2026-06-04 00:00:00 — 2026-07-04 23:59:59`.
- Rabota.ru получил `670` откликов, после дедупликации осталось `656`.
- Pending Sheets: `648` строк уже были дублями, `8` новых строк добавлены.
- Зарплата.ру фаза `2.1` стартовала при включенном source switch, проверила `4` вакансии, загрузила `1714` откликов, выполнила `1039` full resume fetches, нормализовала `593` лида, убрала `872` дубля, сохранила `104`, в Sheets добавила `94`.
- Перед заполнением анкет pending Sheets содержала `10065` неотработанных строк.
- После фикса фильтр периода перед отправкой дал `10065 → 1203` лидов.
- Form proxy перед заполнением подтвердился как `217.29.62.68, RU, Moscow`.

## Наблюдение

До фикса `services/leads_service.py` выставлял `send_respect_period = False` при загрузке pending-очереди из Sheets. Это позволяло старым строкам общей таблицы попадать в заполнение вне выбранного периода.

До фикса `modules/zarplata_api.py` печатал прогресс full resume fetches поврежденной mojibake-строкой и не вызывал `update_progress(current_lead=...)`, поэтому dashboard не имел данных для realtime-строки Зарплата.ру.

Текущий live job был остановлен не ошибкой: timeline содержит `job_stop_requested` в `2026-07-04 15:54:35` и `job_stop` в `15:54:38`. На момент stop было `processed=7`, `sent=3`, `errors=2`, `forms_done=7`, `forms_total=12`.

## Вывод

Root cause невидимого статуса Зарплата.ру: importer публиковал прогресс только в log/stdout, причем одна строка была уже повреждена mojibake в исходнике. Realtime UI читает `progress.current_lead`, поэтому статус не появлялся в стабильной строке полного цикла.

Root cause риска нестрогой даты: pending Sheets queue загружалась целиком и отправлялась с `respect_period=False`.

## Следующий шаг

- После завершения/остановки текущих live jobs выполнять обычный `docker compose up -d --build autolead_bot worker`, потому что hotpatch уже применен в контейнеры без restart, но canonical runtime image должен быть пересобран при следующем безопасном окне.
- Проверить отдельным коротким запуском команды `zarplata`, что dashboard показывает `Зарплата.ру: полные резюме загружены: N` в строке полного цикла/realtime job.
- Отдельно разобрать, кто или что отправило `job_stop_requested` в `2026-07-04 15:54:35`, если пользователь не нажимал stop.

