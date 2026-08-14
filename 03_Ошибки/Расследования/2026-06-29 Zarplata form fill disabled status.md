# 2026-06-29 Zarplata form fill disabled status

## Симптом

В Google Sheets у лидов Зарплата.ру появлялся статус `заполнение выключено`. Такие строки не попадали в общий sender, поэтому анкеты по ним не заполнялись.

## Зона системы

- `modules/zarplata_api.py` — импорт резюме Зарплата.ру и выставление статуса перед выгрузкой в Google Sheets.
- `api/routers/settings.py` — сохранение настроек Зарплата.ру.
- `api/routers/settings_core.py` — нормализация owner-scoped настроек.
- `dashboard/app.js` и `dashboard/index.html` — UI содержит один переключатель `Режим Зарплата.ру`.
- Google Sheets pending/export таблицы текущего owner.

## Гипотеза

Legacy-конфиг мог хранить противоречивое состояние: `zarplata_ru.enabled=true`, но `zarplata_ru.enable_form_fill=false`. UI уже работает как один переключатель, но backend при импорте верил только `enable_form_fill` и записывал dead-status `заполнение выключено`.

## Проверка

- В live-коде `modules/zarplata_api.py` подтверждено: импорт ставил `Статус = заполнение выключено`, если `enable_form_fill=false`.
- В live UI подтвержден один переключатель Зарплата.ру: `dashboard/app.js` отправляет одно состояние в `zarplata_enabled` и `zarplata_enable_form_fill`.
- В live runtime config подтверждено старое состояние у `admin`: `enabled=True`, `enable_form_fill=False`.
- В текущих настроенных Google Sheets для pending/export проверен точный статус `заполнение выключено`: в активной вкладке `Все лиды` таких строк на момент проверки не найдено.

## Наблюдение

Root cause не в Google Sheets и не в sender. Ошибка появлялась раньше, на этапе импорта Зарплата.ру: backend мог выгружать строки с блокирующим статусом из-за устаревшего второго флага.

## Вывод

Канон текущего UI: один переключатель Зарплата.ру включает и сбор, и заполнение. Backend должен нормализовать старые owner-scoped configs и не создавать новые строки со статусом `заполнение выключено`, если источник включен.

Исправлено на live-сервере:

- `modules/zarplata_api.py` теперь считает `enabled=true` достаточным для `form_fill_enabled`.
- `api/routers/settings.py` нормализует `/api/settings/zarplata`: `zarplata_enabled=true` принудительно сохраняет `zarplata_enable_form_fill=true`.
- Live config `admin` мигрирован в `enabled=True`, `enable_form_fill=True`.
- Добавлены regression-тесты в `tests/test_zarplata_api.py` и `tests/test_settings_core.py`.

Проверки:

- `python -m pytest tests/test_zarplata_api.py tests/test_settings_core.py -q` — `15 passed`.
- `docker compose up -d --build autolead_bot worker` — контейнеры пересобраны.
- `https://traffic-hub.pro/api/health` — `200`, `status=ok`.
- GitHub commit TrafficHub: `9b8f51469 Fix Zarplata form fill flag normalization`.

## Следующий шаг

Если пользователь видит старые строки `заполнение выключено` в другой вкладке или таблице, нужно проверить конкретный sheet/tab. В активной настроенной pending-вкладке exact-match этого статуса на момент проверки не найден.

Связано: [[Zarplata.ru integration]]
