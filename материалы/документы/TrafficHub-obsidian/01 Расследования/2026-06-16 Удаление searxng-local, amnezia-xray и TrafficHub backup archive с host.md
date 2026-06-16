# 2026-06-16 Удаление searxng-local, amnezia-xray и TrafficHub backup archive с host

## Симптом

- на хосте оставались лишние runtime-сущности вне продуктового контура `TrafficHub`:
  - контейнер `searxng-local`
  - контейнер `amnezia-xray`
  - архив старых snapshot `/root/TrafficHub_backup_archive`

## Зона системы

- host `150.241.70.31`;
- docker runtime;
- `/opt/searxng-local`;
- `/opt/amnezia/amnezia-xray`;
- `/root/TrafficHub_backup_archive`.

## Гипотеза

Если удалить оба контейнера вместе с их image/mount artifacts и убрать старый backup archive, то host contour станет ближе к реальному рабочему набору проектов вокруг `TrafficHub`.

## Проверка

Перед удалением подтверждено:

- `docker ps` содержал:
  - `searxng-local|searxng/searxng:latest`
  - `amnezia-xray|amnezia-xray:latest`
- mounts:
  - `searxng-local`
    - volume `...fe3d2fbf/_data -> /etc/searxng`
    - bind `/opt/searxng-local/settings.yml -> /etc/searxng/settings.yml`
    - volume `...1eab74d/_data -> /var/cache/searxng`
  - `amnezia-xray`
    - bind `/opt/amnezia/amnezia-xray/clientsTable -> /opt/amnezia/xray/clientsTable`
    - bind `/opt/amnezia/amnezia-xray/server.json -> /opt/amnezia/xray/server.json`
- `/root/TrafficHub_backup_archive` существовал и содержал snapshot `2026-06-11`.

Выполнено root-level удаление:

- `docker rm -f searxng-local amnezia-xray`
- `docker volume rm` для обоих searxng volumes
- `docker image rm searxng/searxng:latest amnezia-xray:latest`
- `rm -rf /opt/searxng-local /opt/amnezia/amnezia-xray /root/TrafficHub_backup_archive`

После удаления подтверждено:

- в `docker ps` больше нет `searxng-local` и `amnezia-xray`
- images отсутствуют
- searxng volumes отсутствуют
- `/opt/searxng-local` отсутствует
- `/opt/amnezia/amnezia-xray` отсутствует
- `/root/TrafficHub_backup_archive` отсутствует

## Наблюдение

- обычного `codex`-доступа для такого cleanup недостаточно;
- root password auth всё ещё нужен для host-level удаления bind paths и root-owned archive;
- после cleanup среди явно видимых внешних runtime-контуров остался только `mfo_api`.

## Вывод

- `searxng-local` и `amnezia-xray` полностью удалены с host;
- старый архив snapshot `TrafficHub` удалён;
- host inventory вокруг `TrafficHub` стал заметно чище.

## Следующий шаг

- поддерживать server inventory в wiki только по live-фактам;
- если потребуется ещё чистка, отдельно проверить, нужны ли на этом host `hermes-*`, `mfo` и `content-poster-bot`.
