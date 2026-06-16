# 2026-06-11 Autolead owner-scoped jobs и UI-логи

## Симптом

- при одновременных `upload/run/send` у разных пользователей в `app_log` и UI появлялись чужие строки;
- в live-логах шёл технический шум: `Retry queue`, `Скриншот ошибки`, `Рассылка: leads=...`, `TrafficHub: sync for user ...`;
- пользователь видел как будто задачи “работают”, но owner-изоляция логов была нарушена.

## Зона системы

- `traffic_hub/worker.py`
- `traffic_hub/services/job_runner.py`
- `api/ws_manager.py`
- `api/server.py`
- `utils/runtime_logging.py`
- `modules/rabota_api.py`
- `modules/vbiv_bot.py`

## Гипотеза

- runtime разрешал несколько job-thread одновременно;
- `job_runner.py` использует `redirect_stdout()`, а `sys.stdout` глобален на весь процесс;
- print-вывод одного job попадал в `_OwnerLogStream` другого job и записывался в чужой `app_log`.

## Проверка

- на production-server поставлены одновременно `upload` для `alex`, `artem`, `artem2`, `debuglogs`;
- до фикса в `app_log` `debuglogs` появлялись строки с периодом `07.06.26-09.06.26` и `-> Заполняем: ...`, характерные для другого owner;
- после фикса worker был пересобран и тот же сценарий повторён;
- дополнительно прогнаны:
  - `admin`: `upload`, `send`, `run`
  - `alex`, `artem`, `artem2`, `debuglogs`: `upload`, короткий `send` со stop, короткий `run` со stop

## Наблюдение

- подтверждено: смешивание происходило именно при параллельном исполнении jobs;
- после перевода worker в режим одного активного job за раз owner-логи перестали протекать между пользователями;
- UI-фильтрация логов стала скрывать технический шум в `app_log` и websocket:
  - `Retry queue: ...`
  - `Скриншот ошибки: ...`
  - `Рассылка: leads=...`
  - `TrafficHub: старт автосинхронизации...`
  - `TrafficHub: sync for user ...`
- `artem2` отдельно подтвердил runtime-проблему данных доступа:
  - `Обновление токена: 401 — неавторизован, токен невалиден, нужна повторная авторизация`
  - это не баг очереди, а невалидный Rabota.ru token для конкретного owner.

## Вывод

- корневая причина смешивания логов была не в Redis/state, а в несовместимости параллельных job-thread с `redirect_stdout()`;
- практическое решение на production: worker исполняет jobs последовательно;
- owner-scoped queue/state в Redis сохранены, но фактический execution сейчас single-active-job per worker-process;
- `artem2` требует повторной авторизации Rabota.ru, иначе `upload/run` продолжают логировать `401`.

## Следующий шаг

- либо сохранить последовательное исполнение как каноническую модель;
- либо перед возвратом к параллельности сначала убрать `redirect_stdout()` из runtime-маршрута и перевести критические `print()` в owner-aware logging;
- отдельно сделать UX-решение для `401` Rabota.ru:
  - либо переводить job в `error`,
  - либо явно поднимать owner-level warning в UI/настройках.

## См. также

- [[03 Плейбуки/Jobs и Worker]]
- [[04 Сущности/Job Queue]]
- [[05 Решения/Очередь задач через Redis и worker]]
