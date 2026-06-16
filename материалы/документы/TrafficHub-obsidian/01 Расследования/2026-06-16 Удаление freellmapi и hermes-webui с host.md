# 2026-06-16 Удаление freellmapi и hermes-webui с host

## Симптом

- на том же сервере, что и `TrafficHub`, оставались два посторонних root-owned проекта:
  - `/root/freellmapi`
  - `/root/hermes-webui`

## Зона системы

- host `150.241.70.31`;
- каталоги `/root/freellmapi` и `/root/hermes-webui`.

## Гипотеза

Если удалить оба каталога root-level доступом и перепроверить их отсутствие обычным `codex`-пользователем, то host contour вокруг `TrafficHub` станет чище и меньше будет путаницы между продуктом и соседними проектами.

## Проверка

- под `codex` подтверждено:
  - оба каталога принадлежат `root:root`
  - права `755`
  - `ACCESS_W=False`
- старый root key больше не принимался по SSH;
- root-вход сработал по password auth;
- выполнено удаление:
  - `rm -rf -- /root/freellmapi /root/hermes-webui`
- после этого обычным `codex`-доступом подтверждено:
  - `/root/freellmapi` отсутствует
  - `/root/hermes-webui` отсутствует
- в `docker ps` не было контейнеров с шаблонами `freellm`, `hermes`, `webui` на момент удаления.

## Наблюдение

- для host-cleanup недостаточно обычного agent SSH path на `codex`;
- legacy root key уже устарел;
- password auth на `root` всё ещё открыт, что само по себе operational risk.

## Вывод

- `freellmapi` и `hermes-webui` удалены с сервера;
- текущий host contour вокруг `TrafficHub` стал уже;
- любые будущие host-level удаления надо считать отдельными инфраструктурными операциями, а не частью live repo `TrafficHub`.

## Следующий шаг

- синхронизировать server inventory в wiki;
- при следующем host-cleanup отдельно решить, нужен ли ещё `hermes-*` контур рядом с `TrafficHub`.
