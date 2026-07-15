# 2026-07-15 read-only аудит live-сервера

Теги: #debug #live #audit

## Симптом

Запрошена полная проверка live-сервера TrafficHub на ошибки с ранжированием от критических до простых.

## Зона системы

- Live host `150.241.70.31`, SSH principal `codex`.
- Server repo `/root/TrafficHub`, Docker Compose, systemd, host resources, PostgreSQL, Redis, Caddy, application logs и публичные health endpoints.
- Связанные заметки: [[05_Эксплуатация/Доступ и подключения]], [[05_Эксплуатация/Развёртывание]], [[06_Отладка/Каталог ошибок]].

## Гипотеза

На live могут присутствовать ошибки runtime, конфигурационный drift или эксплуатационные риски, которые не отражаются одним `/api/health`.

## Проверка

- Выполнена read-only инвентаризация host, repo, containers, healthchecks, logs за 24 часа и 7 дней, systemd, storage, network listeners, PostgreSQL, Redis, SSH и backups.
- Риск-класс: `read-only`; изменения product runtime не выполнялись.

## Наблюдение

- Канонический alias `traffichub-live` в локальном `ssh/config` указывает на отсутствующий ключ профиля `sergk`; рабочий доступ подтверждён прямым fallback-входом с ключом текущего workspace.
- Server repo: branch `main`, HEAD `1a1e3eba4`, рабочее дерево чистое и совпадает с `origin/main`.
- Все 11 Docker-контейнеров работают; 8 контейнеров с healthcheck имеют статус `healthy`; restart count равен `0`, `OOMKilled=false`.
- `traffic-hub.pro/api/health`, `www` и `auth` отвечают успешно. `am /health` возвращает ожидаемый auth boundary `401`. В Caddy за 24 часа не найдено ответов `5xx`.
- PostgreSQL принимает соединения, размер active DB около `105 MB`, `deadlocks=0`. Redis отвечает `PONG`, rejected connections и evictions равны `0`.
- Host load низкий, active swap-in/swap-out во время замера отсутствует. При этом занято `434/511 MiB` swap — след предыдущего memory pressure, не текущий outage.
- Root filesystem заполнен на `75%`. Docker использует `53.22 GB` images и `45.73 GB` build cache, из которых `45.59 GB` reclaimable.
- `freellmapi.service` находится в бесконечном `activating (auto-restart)`: отсутствует `WorkingDirectory=/root/freellmapi`, `NRestarts=14888`, период перезапуска 10 секунд. Unit также содержит sensitive key прямо в `Environment=`; значение в wiki не переносилось.
- SSH effective config: `PermitRootLogin no`, но `PasswordAuthentication yes`; UFW выключен, fail2ban отсутствует. За 24 часа зафиксировано `10713` auth failure events. В просмотренных успешных входах за 7 дней присутствует только public-key auth; evidence успешного password brute-force не найдено.
- В `data/backups` и systemd/cron не найден свежий полный PostgreSQL dump. Последние `.sql` — точечные `alice_cleanup` от `2026-06-21`; deploy script умеет создавать `pre-deploy-*.sql.gz`, но актуальных файлов на host нет.
- Worker за 7 дней: 13 строк `ERROR`; основные причины — неподдерживаемый Office-документ вместо native Google Sheet, отсутствующий лист `Все лиды`, один сбой Playwright driver. Zarplata import 8 раз получил `403 token_expired`; это owner/integration-level деградация, не падение worker.
- Доступны 30 package upgrades, из них Ubuntu сообщает о 3 security updates.
- 92 nginx errors в `operator_crm` — запросы внешнего scanner к несуществующим типовым JS paths; evidence ошибки UI по этим строкам нет.

## Вывод

### Критический риск

1. SSH открыт интернету с password auth, без host firewall и fail2ban, при интенсивном brute-force. Компрометация не подтверждена, но сочетание настроек создаёт прямой риск захвата password-enabled account.

### Высокий приоритет

2. Нет подтверждённого свежего полного backup PostgreSQL и регулярного backup schedule. Сбой диска/volume может привести к невосстановимой потере production data.
3. `freellmapi.service` фактически не работает и перезапущен 14 888 раз; sensitive key хранится inline в unit. Если gateway нужен Telegram bridge, функция недоступна; если не нужен, stale unit создаёт шум и operational debt.

### Средний приоритет

4. Worker частично теряет интеграционные циклы: Zarplata OAuth token expired; Google Sheets target имеет неверный формат/структуру.
5. Docker build cache занимает 45.73 GB, root filesystem уже на 75%; без housekeeping возможен будущий disk-full outage.
6. Не установлены 3 security updates (30 обновлений всего).

### Низкий приоритет

7. Swap занят на 85%, но активного swapping и текущего memory pressure нет.
8. Локальный canonical SSH alias устарел и не работает в текущем профиле.
9. Scanner-generated nginx/Caddy warnings создают шум, но не влияют на health.

На момент аудита текущего production outage нет: основной API, PostgreSQL, Redis и контейнеры работоспособны.

## Следующий шаг

1. В отдельное согласованное окно: отключить SSH password auth, ограничить ingress `22/80/443`, установить rate limiting/fail2ban и проверить доступ новым SSH-сеансом до закрытия текущего.
2. Немедленно создать и проверить restore свежего PostgreSQL dump; затем добавить ежедневное расписание, retention и off-host copy.
3. Решить судьбу `freellmapi`: восстановить рабочую директорию/артефакт либо disable/remove stale unit; вынести и ротировать inline secret.
4. Обновить owner-scoped Zarplata token и исправить Google Sheets document/tab.
5. После проверки используемых images очистить reclaimable build cache и добавить disk alert.
6. Установить security updates с контролируемым reboot/deploy smoke.

## Связанные заметки

- [[03_Плейбуки/Read-only аудит live-сервера]]
- [[05_Эксплуатация/Доступ и подключения]]
- [[05_Эксплуатация/Развёртывание]]
