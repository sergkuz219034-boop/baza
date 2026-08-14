# Read-only аудит live-сервера

## Цель

За один проход отделить production outage от эксплуатационных рисков без изменения runtime.

## Порядок

1. Подтвердить `whoami`, `/root/TrafficHub`, `origin`, `git status`, HEAD и наличие `rg`.
2. Проверить `uptime`, load, RAM/swap, `df -hT`, `df -i`, failed systemd units и journal priority `err`.
3. Проверить все контейнеры: state, health, restart count, OOM flag, stats и `docker system df`.
4. Проверить public health, TLS expiry и Caddy `5xx`.
5. Просмотреть container logs минимум за 24 часа, а worker/integration ошибки — за 7 дней; scanner 404 отделять от product errors.
6. Проверить PostgreSQL readiness, размер DB, rollback/deadlock counters; Redis `PONG`, evictions и rejected connections.
7. Проверить свежесть полного DB backup, расписание, retention и наличие off-host copy. Наличие endpoint или backup-кода не доказывает наличие актуального dump.
8. Проверить SSH effective config, firewall, fail2ban, число auth failures и successful auth methods. Не считать brute-force доказанной компрометацией без успешного входа или другого evidence.
9. Ранжировать находки по impact и likelihood; отдельно перечислить здоровые контуры.

## Безопасность

- Аудит только read-only; не запускать prune, upgrade, restart, backup/restore или изменение firewall без отдельного разрешения.
- Не переносить secret values из env, unit-файлов и container inspect в логи или wiki.
- Для сложных live-команд использовать stdin через SSH-safe wrapper/fallback, а не PowerShell inline interpolation.

## Связанные заметки

- [[03_Ошибки/Расследования/2026-07-15 read-only аудит live-сервера]]
- [[02_Код/Эксплуатация/Доступ и подключения]]
- [[02_Код/Эксплуатация/Развёртывание]]
