# 2026-06-16 Канонический SSH path для Windows ACL и Codex sandbox

## Симптом

- Codex desktop shell не мог подключаться к `codex@150.241.70.31`.
- Появлялись ошибки:
  - `Load key "...": Permission denied`
  - `Permissions ... are too open`

## Зона системы

- локальный Windows SSH client;
- ACL private key;
- различие между human Windows session и Codex sandbox user.

## Гипотеза

Один и тот же private key-path использовался разными локальными учётками, а ACL был пригоден только для одной из них.

## Проверка

- подтверждён текущий пользователь shell: `home\\codexsandboxonline`;
- подтверждено, что `ssh_access/codex_login_ed25519.strict` читается не этим пользователем;
- создана новая копия ключа в `.codex_ssh/codex_login_ed25519` от имени sandbox user;
- на новую копию выставлен owner = `home\\CodexSandboxOnline`;
- на новую копию оставлен только `Read` для этого пользователя;
- выполнен smoke:

```powershell
ssh -i C:\Users\sergk\OneDrive\Desktop\traffichubserver\.codex_ssh\codex_login_ed25519 codex@150.241.70.31 "echo ok && whoami && hostname"
```

## Наблюдение

Проверка прошла успешно:

- `ok`
- `codex`
- `TrafficHub.play2go.cloud`

## Вывод

- Для человека и для AI-агента нельзя считать один и тот же local key-path каноничным.
- Каноническая схема должна быть двухконтурной:
  - `ssh_access/*` — human path;
  - `.codex_ssh/*` — agent path.

## Следующий шаг

- держать актуальную инструкцию в [[server-ssh-access]];
- при каждом onboarding нового разработчика сначала проверять именно его local SSH path и ACL;
- не пытаться "чинить сервер", пока не подтверждён локальный smoke `echo ok && whoami && hostname`.
