# 2026-06-15 Локальный SSH key ACL блокирует server-side доступ

## Симптом

- С рабочего места `C:\Users\sergk\OneDrive\Desktop\traffichubserver` перестал работать вход на `codex@150.241.70.31`.
- `ssh.exe` сообщает:
  - `Load key "...codex_login_ed25519.strict": Permission denied`
  - `Permission denied (publickey)`
- Python/Paramiko также не может открыть private key-файлы на чтение.

## Зона системы

- Локальный Windows host
- Папка `ssh_access/`
- SSH bootstrap до входа на сервер

## Гипотеза

- После локальной чистки и переноса ключей в `ssh_access/` сломались ACL/ownership на private key-файлах.

## Проверка

- Подтверждено локально:
  - чтение `ssh_access/codex_login_ed25519`
  - чтение `ssh_access/codex_login_ed25519.strict`
  обе операции падают с `PermissionError: [Errno 13] Permission denied`
- `ssh -i ...codex_login_ed25519.strict codex@150.241.70.31 "echo ok"` не проходит уже на этапе чтения ключа.
- `ssh-agent` на машине не запущен и не может служить обходом.
- Старый путь `artifacts/ssh/...` больше не существует.
- После правки ACL из реального Windows-профиля подтверждён live-check:
  - `ssh -i C:\Users\sergk\OneDrive\Desktop\traffichubserver\ssh_access\codex_login_ed25519.strict codex@150.241.70.31 "hostname && whoami"`
  - ответ: `TrafficHub.play2go.cloud` / `codex`

## Наблюдение

- Host, user и fingerprint в wiki согласованы и выглядят корректно.
- Локальный `ssh_access/config` переведен на `ssh_access/codex_login_ed25519.strict`.
- Блокер находится до сетевого рукопожатия с сервером.
- Фикс восстановил доступ именно для рабочего Windows-профиля `HOME\sergk`.
- Текущая сессия Codex desktop использует отдельную sandbox-учётку `HOME\codexsandboxonline`; это отдельный runtime-контур и его не нужно автоматически наделять доступом к private key.

## Вывод

- Первопричина была локальной: ACL Windows на private key-файлах в `ssh_access/`, а не сервер `150.241.70.31`.
- После исправления ACL доступ по SSH восстановлен для рабочего профиля `HOME\sergk`.
- Для документации нужно различать два контекста:
  - реальный пользовательский Windows-профиль;
  - sandbox-пользователь Codex desktop.

## Следующий шаг

- Считать `ssh_access/codex_login_ed25519.strict` снова каноническим рабочим ключом.
- При повторении `Permission denied` сначала проверять, из какого именно Windows-пользователя выполняется команда.
- Server-side работы возвращать к обычному порядку: `codex` + `sudo`, без возврата к `root` как основному входу.
