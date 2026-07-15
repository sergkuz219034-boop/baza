# 2026-07-15 SSH key-only и UFW ingress

## Проблема

Live host принимал password SSH authentication, не имел host firewall и получал более 10 тыс. auth failure events в сутки.

## Контекст

`codex`, `codexops` и `sergey` имеют authorized keys. Успешные входы из проверенного периода были key-based. Public product требует только TCP `80/443`; управление host — TCP `22`.

## Решение

- Разрешить SSH только через public key: `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `AuthenticationMethods publickey`, `PermitRootLogin no`.
- Поместить policy в начало `/etc/ssh/sshd_config`, до cloud-init include.
- Включить UFW: default incoming deny; limit SSH 22; allow HTTP 80 и HTTPS 443.

## Последствия

- Password-only клиенты больше не могут подключаться; пользователю без рабочего private key требуется out-of-band восстановление доступа.
- SSH brute-force ограничен firewall до передачи в sshd.
- Новые сервисы с inbound port требуют явного UFW rule и проверки exposure.

## Альтернативы

- Оставить password auth и добавить fail2ban: снижает шум, но не закрывает риск слабого/утёкшего пароля.
- Разрешать SSH только с fixed source IP: сильнее, но несовместимо с динамическими IP текущих операторов.
- Cloud firewall без UFW: полезный дополнительный слой, но не заменяет host-local policy.

## Проверка

- Новый key-only SSH session успешен.
- Password-only SSH session отклонён.
- `sshd -t` успешен, `ssh.service` active.
- `https://traffic-hub.pro/api/health` вернул `200` после UFW enable.
