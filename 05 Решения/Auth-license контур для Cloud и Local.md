# Auth-license контур для Cloud и Local

## Проблема

TrafficHub больше нельзя описывать только как серверный SaaS. В проекте остаётся local/download контур: `TrafficHub.exe`, `update.exe`, local secrets/config, activation key и callback `http://localhost:8080/auth/callback`.

Из-за этого `license_auth` и `license_server` нельзя удалять как мусор только потому, что live production сейчас работает через `traffic-hub.pro`.

## Контекст

Подтверждено по live `/root/TrafficHub` 2026-07-02:

- `docker-compose.yml` содержит сервисы `license_auth` и `license_server`;
- live containers `traffichub_license_auth` и `traffichub_license_server` healthy;
- `/health` на `127.0.0.1:8400` и `127.0.0.1:8401` возвращает `ok`;
- `auth.traffic-hub.pro` проксируется в `license_auth`;
- `license_server` не публикуется как UI, но остаётся внутренним license API / local-download кандидатом.

## Решение

- Считать TrafficHub двухконтурным продуктом: `Cloud/SaaS` + `Local/download`.
- Оставить `license_auth` и `license_server` до отдельного аудита local activation/update flow.
- Не переименовывать контейнеры косметически без compatibility check по scripts, Caddy, healthchecks, README и local workflow.
- Оптимизировать build через общий root Python image, но не объединять процессы `app`, `worker`, `license_auth`, `license_server`.

## Последствия

- Cleanup-задачи больше не имеют права удалять license-контур “по ощущению”.
- Любое удаление `license_server`, `utils.license`, `TrafficHub.exe` или `update.exe` требует отдельного ADR.
- Production cloud можно упрощать без потери local/download сценария.

## Альтернативы

- Удалить `license_server` как legacy: отклонено до аудита local/download, потому что риск сломать activation/update flow выше выигрыша от удаления.
- Слить `license_auth` и `license_server`: возможно позже, но только после карты endpoints и совместимости с локальной версией.

