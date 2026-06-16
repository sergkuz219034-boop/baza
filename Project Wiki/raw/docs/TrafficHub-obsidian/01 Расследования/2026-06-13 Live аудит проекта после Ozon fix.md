## Симптом

- Требовалось проверить текущее состояние всего live-проекта после серии правок, связанных с Ozon, логами, прокси и runtime.
- Был риск, что часть системы находится в рабочем состоянии только “визуально”, но не подтверждена health/runtime-проверками.

## Зона системы

- `/root/TrafficHub/docker-compose.yml`
- контейнеры:
  - `autolead_server_bot`
  - `traffichub_worker`
  - `traffichub_account_manager`
  - `traffichub_caddy`
  - `traffichub_postgres`
  - `traffichub_redis`
- user config storage:
  - `utils/control_store.py`
  - PostgreSQL `control_user_app_configs`

## Гипотеза

- После точечных hotfix часть проверок могла быть устаревшей:
  - host-level health на старом порту;
  - proxy parser мог оставлять legacy-конфиги частично битым;
  - в боевом дереве могли остаться временные backup-файлы.

## Проверка

- Проверен `docker ps` и статусы контейнеров.
- Проверены host/public health endpoints.
- Проверен `docker-compose.yml` на актуальный published port и healthcheck.
- Выполнен `python3 -m compileall -q api modules services traffic_hub utils config AccountManager`.
- Проверены логи:
  - `autolead_server_bot`
  - `traffichub_worker`
  - `traffichub_account_manager`
- Проверены user-configs через `utils.control_store.load_user_config()` на:
  - legacy malformed `proxy_url`;
  - старые Ozon routes `pid=41266` / `pid=4161` для `offer_id=22`.
- Удалены временные `.bak-*`, созданные в ходе серверных hotfix.

## Наблюдение

- `autolead_server_bot` healthy.
- `traffichub_worker` healthy.
- `traffichub_account_manager` healthy.
- Public health:
  - `https://traffic-hubcrm.ru/api/health` -> `200`
  - `https://am.traffic-hubcrm.ru/api/health` -> `200`
- Host health для Autolead должен проверяться по `127.0.0.1:8080`, а не по `127.0.0.1:8000`.
- `docker-compose.yml` подтверждает:
  - publish: `127.0.0.1:${APP_PORT:-8080}:8080`
  - healthcheck: `curl -sf http://localhost:8080/api/health`
- `jobs/status` без auth отдаёт `401`, это штатное поведение, не авария.
- `compileall` прошёл без ошибок.
- В production image нет `pytest`; это означает не runtime bug, а то, что текущий prod-container не является test image.
- После финальных proxy-fix не найдено оставшихся user-config поломок по шаблонам:
  - malformed HTTP proxy
  - старые Ozon routes для `offer_id=22`
- Временные `.bak-*` из сегодняшних hotfix удалены.

## Вывод

- На момент проверки подтверждённых критических runtime-поломок в проекте не выявлено.
- Основные сервисы проекта живы и отвечают корректно.
- Ozon-fix доведён до рабочего состояния на уровне route + proxy parser + runtime smoke.
- Ошибка с `127.0.0.1:8000` оказалась не проблемой проекта, а устаревшей точкой проверки: текущий port для Autolead — `8080`.
- Production runtime сейчас чище:
  - без временных `.bak-*`,
  - без подтверждённых legacy proxy-config проблем,
  - без старого disabled Ozon route в активных user-configs.

## Следующий шаг

- Если нужен полноценный регрессионный test-run, его нужно выполнять не в production image, а в dev/test окружении с установленным `pytest`.
- Для дальнейших аудитов использовать как базовые канонические проверки:
  - `https://traffic-hubcrm.ru/api/health`
  - `https://am.traffic-hubcrm.ru/api/health`
  - `http://127.0.0.1:8080/api/health` на сервере
