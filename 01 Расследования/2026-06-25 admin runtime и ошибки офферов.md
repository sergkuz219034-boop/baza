# 2026-06-25 admin runtime и ошибки офферов

## Симптом

- В `Admin панель -> Тех работы` появлялась ошибка `message is not defined`.
- Блок `Обновление из GitHub` показывал старый commit контейнера, хотя серверный repo уже был обновлён.
- `Runtime Inspector` оставался в состоянии `Не загружено`, пока admin вручную не нажмёт кнопку проверки.
- В логах партнёрских сетей повторялась ошибка Lovko sync: `_import_lovko_offer_stats() got an unexpected keyword argument 'tenant_id'`.
- При заполнении формы Leads.su ошибка `форма не подтверждена после отправки` считалась постоянной и не попадала в retry queue.

## Зона системы

- `/root/TrafficHub/dashboard/app.js`
- `/root/TrafficHub/api/routers/system.py`
- `/root/TrafficHub/traffic_hub/api/routers/integrations.py`
- `/root/TrafficHub/modules/vbiv_bot.py`
- контейнеры `autolead_server_bot`, `traffichub_worker`

## Гипотеза

- Фронт техработ обращается к удалённому input-полю `message`.
- GitHub-блок читает `.git` внутри контейнера, который не обновляется при hotfix-копировании файлов.
- Runtime Inspector не вызывается автоматически при открытии admin-раздела.
- Lovko sync вызывает функцию с `tenant_id`, но функция не принимает этот аргумент.
- Классификация form-failure слишком агрессивная для живых лендингов.

## Проверка

- Проверен live server repo: `git rev-parse --short HEAD`.
- Проверены файлы в live repo и контейнере.
- Запущены контейнерные тесты: `tests/test_settings_maintenance.py`, `tests/test_integrations_sync.py`, `tests/test_leadsu_blank_recovery.py`.
- Проверены свежие логи `autolead_server_bot` после рестарта.
- Проверены системные функции внутри контейнера: `_repo_commit`, `runtime_inspector`, `git_status`.

## Наблюдение

- `dashboard/app.js` в `saveMaintenanceMode()` содержал строку `if (message) message.value = ...`, но переменной `message` больше нет.
- `api/routers/system.py` читал commit через `git rev-parse HEAD` внутри `/app`; при hotfix-деплое через `docker cp` `.git` контейнера остаётся stale.
- `_import_lovko_offer_stats()` не принимала `tenant_id`, хотя `_sync_network()` передавал его.
- При переносе legacy Lovko rows owner менялся, но `tenant_id` оставался старым.
- `modules/vbiv_bot.py` считал `форма не подтверждена после отправки` постоянной ошибкой, хотя на live лендингах это может быть transient-сбой подтверждения.

## Вывод

Подтверждено кодом и runtime:

- ошибка техработ была фронтовой;
- stale commit был следствием deploy-модели `docker cp`, а не отставания GitHub;
- Lovko sync ломался из-за несовместимой сигнатуры функции;
- часть form-fill ошибок преждевременно исключала retry queue.

Исправлено в TrafficHub commit `5d9fc210a`.

## Следующий шаг

- После следующих hotfix-деплоев писать актуальный commit в `/app/.deploy_commit`.
- При новых ошибках форм отличать постоянные ошибки валидации от временного неподтверждения submit.
- Для full-cycle проблем сначала смотреть [[Runtime Inspector]], затем [[Job Timeline]] и persistent `app_log`.

## Связанные заметки

- [[Runtime Inspector]]
- [[TrafficHub deployed commit marker]]
- [[Lovko sync]]
- [[Form-fill retry classification]]
