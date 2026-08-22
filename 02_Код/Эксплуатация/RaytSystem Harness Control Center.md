# RaytSystem Harness Control Center

С 2026-08-22 интерфейс управления Harness — RaytSystem-derived control center.
Он является stateless UI и governed-command client; каноническими источниками
остаются Agent-OS, Codex, Graphify, Headroom, Caveman, Ponytail, CodeBurn и Wiki.

## Live

- merge SHA: `a428044bd8d06354e09ab9d417d45b45325e41f9`;
- service: `traffichub-raytsystem.service`;
- bind: только `127.0.0.1:8766`;
- health: `curl -fsS http://127.0.0.1:8766/healthz`;
- immutable release: `/opt/traffichub-raytsystem/a428044bd8d06354e09ab9d417d45b45325e41f9`;
- canonical state: `/root/TrafficHub/state`.

UI не содержит собственных SQLite/ledger и не запускает Codex, shell, Git,
Docker, deploy или DB-команды напрямую. LOW_RISK-команды проходят через
Agent-OS lifecycle gates и записывают decisions/history в canonical state.

## Windows

Клиент установлен в `%LOCALAPPDATA%\TrafficHub\RaytSystem\client-a428044b`.
Запуск туннеля:

```powershell
& "$env:LOCALAPPDATA\TrafficHub\RaytSystem\client-a428044b\windows\Start-RaytSystem.ps1" `
  -Mode Tunnel -LocalPort 8766 `
  -SshConfig "C:\Users\admin\Desktop\Project\ssh\config"
```

Открыть `http://127.0.0.1:8766/`. Остановка:

```powershell
& "$env:LOCALAPPDATA\TrafficHub\RaytSystem\client-a428044b\windows\Stop-RaytSystem.ps1"
```

Launcher использует native Windows `ssh.exe`; WSL не требуется. Preview ищет
рабочий `py -3.12`, затем использует Python 3.12 из `uv`.

## Проверка и rollback

Проверить service, health, точные 10 пунктов меню и 8 систем. Rollback —
переключить systemd unit на предыдущий immutable release SHA и повторить health.
Удалённый старый control center не восстанавливать как источник состояния.
