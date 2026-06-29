# 2026-06-29 Unified Rabota and Zarplata dispatch order

## Симптом

Пользовательское требование: выгрузка Зарплата.ру должна начинаться сразу после выгрузки Rabota.ru, а затем должна идти одна общая рассылка по лидам обоих источников.

## Зона системы

- `traffic_hub/services/job_runner.py`
- `services/leads_service.py`
- `modules/zarplata_api.py`
- Google Sheets pending-таблица
- worker container `traffichub_worker`

## Гипотеза

До фикса Зарплата.ру запускалась в `job_runner` перед `run_full_cycle()`, поэтому фактический порядок был неканонический: Зарплата.ру могла отрабатывать до Rabota.ru, а общая рассылка жила внутри Rabota-oriented полного цикла.

## Проверка

Подтверждено чтением live server repo `/root/TrafficHub`:

- `traffic_hub/services/job_runner.py` для `run/automode` вызывал `run_zarplata_import()` до `run_full_cycle()`.
- `services/leads_service.py::run_full_cycle()` выполнял Rabota.ru scrape, Rabota.ru Sheets upload и затем sender.
- Зарплата.ру не была встроена между Rabota.ru upload и sender.

## Наблюдение

Фактический порядок был неудобен для общего sender:

1. Зарплата.ру могла выгрузить строки до Rabota.ru.
2. Rabota.ru затем выгружала свои строки.
3. Sender загружал pending-очередь уже внутри полного цикла, но ownership порядка был размазан между `job_runner` и `leads_service`.

## Вывод

Канон после commit `d2c4c0256`:

`Rabota.ru сбор -> Rabota.ru Google Sheets -> Зарплата.ру Google Sheets -> общая рассылка из pending-таблицы`

Реализация:

- `job_runner` больше не запускает Зарплата.ру перед `run_full_cycle()`.
- `leads_service.run_full_cycle()` запускает Зарплата.ру после фазы 2 Rabota.ru и до фазы 3 общей рассылки.
- Команда `upload` сохраняет порядок источников: Rabota.ru сначала, Зарплата.ру после неё, без sender.
- Owner guard остался прежним: `enabled && client_id && client_secret && access_token`.

## Проверка результата

На сервере выполнены тесты:

```text
python -m pytest tests/test_zarplata_owner_guard.py tests/test_leads_service_sheets_flow.py tests/test_zarplata_api.py -q
22 passed
```

Контейнеры пересобраны и перезапущены:

- `autolead_bot` / `traffichub_app`
- `worker` / `traffichub_worker`

Health-check API:

```text
GET http://127.0.0.1:8080/api/health -> {"status":"ok","version":"1.2","app":"TrafficHub"}
```

## Следующий шаг

Если пользователь увидит старый порядок в UI-логах, проверить, что job создан после деплоя commit `d2c4c0256`, а не является продолжением старого worker-run.

## Связанные заметки

- [[Zarplata.ru integration]]
- [[2026-06-29 Zarplata owner readiness guard]]
- [[2026-06-29 Zarplata form fill disabled status]]
