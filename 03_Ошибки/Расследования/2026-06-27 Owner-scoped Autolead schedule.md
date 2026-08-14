# 2026-06-27 Owner-scoped Autolead schedule

## Симптом

Нужно проверить, что расписание Autolead индивидуальное для каждого пользователя и применяется так, как пользователь выставил в своих настройках.

## Зона системы

- `services/leads_service.py`
- `api/routers/settings.py`
- `api/routers/settings_core.py`
- PostgreSQL `control_user_app_configs.config_json`
- worker job queue через `job_queue.enqueue_job(owner, "run", source="schedule")`

## Гипотеза

Настройки расписания сохраняются owner-scoped, но scheduler мог использовать один общий набор `schedule_times` и запускать всех schedulable users по чужому времени.

## Проверка

- Проверена БД: `control_user_app_configs` хранит `schedule_enabled` и `schedule_times` отдельно по `login`.
- Проверен код сохранения: `schedule_enabled` и `schedule_times` находятся в `EDITABLE` и пишутся в owner-bound settings flow.
- Проверен runtime helper scheduler в `services/leads_service.py`.
- Проверен live-план внутри контейнера `traffichub_app` после rebuild.

## Наблюдение

До фикса scheduler регистрировал jobs по одному effective scheduler config, а при срабатывании делал fan-out по всем owner. Это ломало индивидуальность времени: owner мог попасть в запуск по времени другого owner.

Live snapshot после фикса:

```text
{'13:00': ['admin'], '18:00': ['admin'], '21:00': ['admin']}
(('13:00', ('admin',)), ('18:00', ('admin',)), ('21:00', ('admin',)))
```

Это означает: сейчас schedulable только `admin`; users с `schedule_enabled=false` или пустым `schedule_times` не попадают в план.

## Вывод

Индивидуальность хранения была, индивидуальность исполнения scheduler была неполной. Исправлено: scheduler строит owner-scoped plan `time -> owners` и в конкретное время запускает только тех owner, у кого это время сохранено и включено.

## Исправление

- `services/leads_service.py`: добавлен `_collect_scheduler_plan()` и `_scheduler_plan_signature()`.
- `_scheduled_job(scheduled_time)` теперь получает конкретное время и выбирает owner'ов только для него.
- `_register_all_jobs()` регистрирует все уникальные owner-scoped времена.
- Добавлены regression tests в `tests/test_scheduler_config.py`.

## Проверка после исправления

- `python -m pytest tests/test_scheduler_config.py tests/test_jobs_router.py tests/test_job_queue_transition.py tests/test_settings_core.py tests/test_access.py tests/test_autolead_access.py tests/test_leads_service_sheets_flow.py -q`
- Результат: `53 passed`.
- Live rebuild: `docker compose up -d --build autolead_bot worker`.
- `/api/health` на `traffic-hub.pro` вернул `ok`.
- Стабильное окно логов после rebuild без новых ошибок.

## Следующий шаг

Если пользователь вручную включает расписание и задаёт времена, проверить live-план внутри `traffichub_app`: `_collect_scheduler_plan({})` должен показать этого owner только в его временах.
