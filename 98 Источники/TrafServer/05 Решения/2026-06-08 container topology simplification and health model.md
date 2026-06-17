## Контекст

На сервере TrafficHub контейнерная схема постепенно разрасталась: сервисы делили слишком широкие volume mounts, использовали отдельную сеть для связей, которые можно было держать в базовых сетях, а фоновые процессы были хуже наблюдаемы, чем HTTP-сервисы.

На 8 июня 2026 задача была не просто проверить, что контейнеры "живы", а упростить структуру так, чтобы:

- каждый сервис видел только действительно нужные ему данные;
- сетевые связи были минимально достаточными;
- worker имел явный runtime-health, а не только факт, что процесс внутри контейнера не завершился.

## Что подтверждено по коду и рантайму

- `license_auth` аутентифицирует пользователей через PostgreSQL и приватный RSA key, а не через локальный `control.db`.
- `AccountManager` не использует общий каталог `secrets` TrafficHub.
- `autolead_bot` должен видеть `account_manager` по внутреннему DNS-имени.
- `caddy` должен видеть `account_manager` только как upstream reverse-proxy.
- `worker` раньше не имел отдельной health-модели: Docker видел лишь то, что контейнер не упал.

## Решение

На live-сервере применены следующие изменения:

1. Убран лишний shared mount:
- `license_auth` больше не монтирует общий `./data`;
- `account_manager` больше не монтирует общий `./secrets`.

2. Упрощена сетевая топология:
- удалена отдельная `account_manager_net`;
- `autolead_bot` теперь работает в `core_net` и `edge_net`;
- `account_manager` теперь работает в `core_net` и `edge_net`;
- `caddy` остаётся только в `edge_net`.

3. Улучшена наблюдаемость worker:
- в `traffic_hub/worker.py` добавлен heartbeat-файл `worker.heartbeat`;
- worker обновляет heartbeat в рантайме;
- в compose добавлен healthcheck worker по freshness heartbeat-файла.

4. Дочищена конфигурация:
- из `license_auth` удалён устаревший `CONTROL_DB_PATH`, который больше не соответствовал его реальному источнику истины.

5. Разделены системные и runtime-secrets:
- `config.json`, `rabota_tokens.json`, `service_account.json` и user-scoped `service_account__*.json` перенесены в `data/runtime/secrets/`;
- `secrets/` оставлен под системные артефакты установки: `.hwid`, `.salt_cache`, `traffic_hub_jwt_secret.key`, `license_*` keys и related server secrets;
- `autolead_bot` и `worker` переведены на `CONFIG_FILE`, `TOKEN_FILE`, `GS_SERVICE_ACCOUNT_FILE` из `data/runtime/secrets`;
- у `worker` системный `secrets` mount переведён в read-only, потому что его рабочие кэши уже не живут в этом каталоге.

## Последствия

Плюсы:

- меньше скрытых зависимостей между сервисами;
- меньше риск, что соседний контейнер случайно читает чужие runtime-данные;
- проще reasoning по сетям: `core_net` для внутренних сервисных вызовов, `edge_net` для reverse-proxy и публичных точек входа;
- worker теперь видно как действительно healthy/unhealthy, а не просто "container still running".
- runtime-кэши пользователя теперь отделены от системных ключей сервера и их проще бэкапить/мигрировать отдельно.

Минусы и остаточный долг:

- `autolead_bot` и `worker` всё ещё используют общий каталог `./secrets`, потому что часть runtime-кэшей и ключей пока завязана на эту структуру;
- `autolead_bot` всё ещё имеет rw-доступ к системному `secrets/`, потому что эта установка сохраняет server identity (`.hwid`, `.salt_cache`) в этом каталоге;
- локальный snapshot нужно периодически переснимать после infra-изменений; на 8 июня 2026 `remote_server_snapshot/` был синхронизирован с live-сервером по ключевым файлам (`docker-compose.yml`, `traffic_hub/worker.py`, `config/settings.py`);
- часть документации по volumes и сетям нужно будет пересинхронизировать отдельно.

## Проверка после применения

После переподнятия сервисов на сервере подтверждено:

- `autolead_server_bot` healthy;
- `traffichub_worker` healthy;
- `traffichub_license_auth` healthy;
- `traffichub_account_manager` healthy;
- `https://auth.traffic-hubcrm.ru/health` отвечает `200`;
- `https://am.traffic-hubcrm.ru/api/health` отвечает `200`;
- heartbeat-файл worker создаётся и обновляется в `data/runtime/worker.heartbeat`.

## Почему это решение лучше предыдущего

Предыдущая схема работала, но была "шире", чем нужно. Это увеличивало когнитивную сложность и усложняло отладку: приходилось помнить не только кто с кем общается, но и какие контейнеры потенциально могут читать общий runtime-state.

Новая схема не меняет продуктовую логику, но делает инфраструктурную модель ближе к реальной:

- auth-сервис получает только auth-зависимости;
- account manager отделён от секретов TrafficHub;
- worker получил собственный признак жизнеспособности;
- отдельная сеть убрана там, где двух базовых сетей достаточно.
