# Remote ops tools

## Назначение

Локальные утилиты в `tools/` для безопасной работы с live-сервером TrafficHub без локального git-клона приложения.

## Подтверждённые файлы

- `tools/local_ssh.py` — создаёт SSH-клиент через Paramiko.
- `tools/remote_exec.py` — выполняет команду или shell-скрипт на сервере.
- `tools/remote_bash.ps1` — PowerShell-wrapper над `remote_exec.py`.

## Подтверждённое исправление Unicode

`tools/remote_exec.py` должен:

- загружать shell-скрипты на сервер байтами UTF-8 через SFTP `wb`;
- заменять некорректные Windows surrogate codepoints на `?`, а не падать;
- декодировать server stdout/stderr как UTF-8;
- писать локальный stdout/stderr как UTF-8, чтобы русские логи и JSON не превращались в mojibake.

На сервере также создан `/usr/local/bin/python -> /usr/bin/python3`, чтобы команды и scripts не зависели от отсутствия бинаря `python`.

## Текущая модель SSH

По умолчанию используется:

- host: `150.241.70.31`
- user: `codex`
- key: `.tmp_ssh_archive/ssh/.codex_ssh/codex_login_ed25519.current`

Переопределение через env:

- `TRAFSERVER_HOST`
- `TRAFSERVER_USER`
- `TRAFSERVER_KEY_PATH`
- `TRAFSERVER_PASSWORD`
- `TRAFSERVER_PARAMIKO_PATH`

## Почему не raw ssh из PowerShell

PowerShell интерпретирует спецсимволы до передачи команды в SSH. Это создаёт нестабильные ошибки при server-debug задачах. Поэтому сложный bash передаётся через `remote_exec.py --stdin` или `--file`.

## Связанные плейбуки

- [[Безопасное выполнение серверных команд без PowerShell quoting]]
- [[Runtime doctor]]
