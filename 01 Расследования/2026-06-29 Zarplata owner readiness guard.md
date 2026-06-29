# 2026-06-29 Zarplata owner readiness guard

## Симптом

Нужно подтвердить, что Зарплата.ру выгружается только у того пользователя, у которого заполнены данные приложения и включён переключатель.

## Зона системы

- `traffic_hub/services/job_runner.py` — подключает Зарплата.ру к командам `upload`, `run`, `automode`.
- `modules/zarplata_api.py` — прямой запуск `run_zarplata_import()`.
- `services/leads_service.py` — owner-scoped config load.
- `tests/test_config_merge.py` — защита от наследования admin-настроек Зарплата.ру обычным user-профилем.

## Гипотеза

Owner isolation по config уже есть, но runtime guard был недостаточно строгим: `upload/run` смотрели только `zarplata_ru.enabled`, а не полноту подключения приложения и user OAuth token.

## Проверка

Подтверждено live-кодом до фикса:

- `traffic_hub/services/job_runner.py` запускал `run_zarplata_import(config)`, если `zarplata_ru.enabled=true`.
- `modules/zarplata_api.py` пропускал `enabled=false` и отсутствие user `access_token`, но не требовал `client_id/client_secret`.
- `tests/test_config_merge.py` уже проверял, что user-профиль не наследует admin `zarplata_ru`.

Runtime-снимок после проверки:

- `admin`: `enabled=True`, `client_id=True`, `secret=True`, `user_token=True`, `READY=True`.
- `Artem`: `enabled=False`, `client_id=True`, `secret=True`, `user_token=False`, `app_token=True`, `READY=False`.
- `artem`: `enabled=False`, `client_id=True`, `secret=True`, `user_token=False`, `app_token=True`, `READY=False`.
- `alex`, `ARTEM2`, `seregalys`, `sergkuz2190`: `READY=False`.

## Наблюдение

App-token (`client_credentials`) не считается достаточным для выгрузки резюме. Для реальной выгрузки нужен user OAuth `access_token`, полученный через работодателя.

## Вывод

Канон запуска Зарплата.ру:

`ready = enabled && client_id && client_secret && access_token`

Если хотя бы одного условия нет, Зарплата.ру не должна запускаться из `upload/run/automode` и не должна выгружать резюме при прямом запуске.

Исправлено:

- `traffic_hub/services/job_runner.py` получил `_zarplata_ready_for_owner()` и больше не запускает Зарплата.ру из `upload/run`, если owner не готов.
- `modules/zarplata_api.py` теперь возвращает `reason=missing_app_credentials`, если источник включён, но нет `client_id/client_secret`.
- Добавлены regression-тесты `tests/test_zarplata_owner_guard.py`.

Проверки:

- `python -m pytest tests/test_zarplata_owner_guard.py tests/test_zarplata_api.py tests/test_config_merge.py -q` — `27 passed`.
- Контейнеры `autolead_bot` и `worker` пересобраны и healthy.
- `/api/health` — `ok`.
- GitHub commit TrafficHub: `d8e0206f4 Guard Zarplata import by owner readiness`.

## Следующий шаг

Если Зарплата.ру должна работать у `Artem`, нужно получить именно user OAuth token работодателя через authorization code. Одного app-token недостаточно.

Связано: [[Zarplata.ru integration]]
