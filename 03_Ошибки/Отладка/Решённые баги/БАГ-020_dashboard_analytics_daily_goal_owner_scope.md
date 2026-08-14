# БАГ-020: dashboard analytics читала `daily_goal` не из owner-scoped конфига

## Симптом

В аналитике и на dashboard user мог видеть цель дня (`daily_goal`) не из своих настроек, а из общего runtime-конфига.

Практический эффект:

- progress bar и подпись `цель: X / день` могли показывать не своё значение;
- линия `Минимум ...` на графике `Лиды по дням` могла строиться по чужой цели;
- баг затрагивал не одного пользователя, а весь owner-scoped контур, если значения `daily_goal` различались между профилями.

## Зона системы

- `services/stats_service.py`
- `api/routers/stats.py`
- `dashboard/app.js`

## Гипотеза

Аналитика summary/history уже была owner-scoped по runtime-таблицам, но сама цель дня бралась не из owner-profile, а из общего `config.json`.

## Проверка

- В `services/stats_service.py` до фикса `_load_daily_goal()` читал `settings.CONFIG_FILE` напрямую.
- `api/routers/stats.py` корректно входил в `bind_current_username(_.username)`, но это не влияло на `_load_daily_goal()`, потому что она обходила owner-scoped `load_config()`.
- После фикса `_load_daily_goal()` переведён на `services.leads_service.load_config()`, который уже читает owner-scoped профиль внутри user-context.
- В runtime container прогнан набор тестов:
  - `tests/test_stats_service.py`
  - `tests/test_leads_service_sheets_flow.py`
  - `tests/test_config_merge.py`
- Результат: `18 passed`.

## Наблюдение

Live-проверка после deploy `ac66da2`:

- `admin -> daily_goal=500`
- `alex -> daily_goal=500`
- `artem -> daily_goal=500`
- `kursmerkusheva@gmail.com -> daily_goal=0`

Это подтвердило, что summary теперь возвращает owner-scoped значение, а не одно общее число для всех.

Отдельно проверено, что `alex` в runtime-summary всё ещё имеет `total_leads=0` и `processed_today=0`, но это уже не баг `daily_goal`: в PostgreSQL runtime-таблицах у него действительно нет owner-scoped `autolead_leads` и `autolead_send_history`, есть только `autolead_run_log`.

## Вывод

Проблема была не в frontend и не в графиках как таковых, а в том, что один analytics field обходил owner-scoped config boundary.

После фикса:

- `daily_goal` в analytics/dashboard читается через owner-scoped `load_config()`;
- текущие пользователи и будущие owner-profile больше не должны наследовать цель дня из общего runtime-конфига;
- если analytics у конкретного пользователя всё ещё пустая, дальше нужно проверять уже owner-scoped runtime-данные (`autolead_leads`, `autolead_send_history`, `autolead_run_log`), а не `daily_goal`.

## Следующий шаг

- при жалобах на пустую аналитику различать:
  - bug в owner-scoped config (`daily_goal`, settings, bindings);
  - bug в runtime data ownership (`autolead_leads`, `autolead_send_history`, `autolead_run_log`);
- отдельно документировать и расследовать сценарии, где run-log у owner есть, а leads/send-history пусты.
