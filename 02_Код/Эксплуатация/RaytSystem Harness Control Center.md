# RaytSystem Harness Control Center

С 2026-08-23 интерфейс управления Harness использует официальный web UI
RaytSystem Public OS, закреплённый на revision
`b5ac70560112758f78dd15852422ee697ac336f4`, с минимальным TrafficHub overlay.
Он является stateless UI и governed-command client; каноническими источниками
остаются Agent-OS, Codex, Graphify, Headroom, Caveman, Ponytail, CodeBurn и Wiki.

## Live

- merge SHA: `7e85a8baf6c056b75a441262e156492a7cb2bef7`;
- service: `traffichub-raytsystem.service`;
- bind: только `127.0.0.1:8766`;
- health: `curl -fsS http://127.0.0.1:8766/healthz`;
- immutable release: `/opt/traffichub-raytsystem/7e85a8baf6c056b75a441262e156492a7cb2bef7`;
- canonical state: `/root/TrafficHub/state`.

UI не содержит собственных SQLite/ledger и не запускает Codex, shell, Git,
Docker, deploy или DB-команды напрямую. LOW_RISK-команды проходят через
Agent-OS lifecycle gates и записывают decisions/history в canonical state.
HTTP mutation требует loopback Host/Origin, same-origin session cookie, CSRF и
`Idempotency-Key`; повтор ключа с другим payload отклоняется.

Overlay сохраняет композицию официального Command Center: сгруппированную
навигацию, hero с орбитой, панели внимания, активной работы, последних запусков
и агентов. Raw JSON-представление и подмена upstream `main.tsx` не используются.

## Windows

Клиент установлен в `%LOCALAPPDATA%\TrafficHub\RaytSystem\client-7e85a8ba`.
Запуск туннеля:

```powershell
& "$env:LOCALAPPDATA\TrafficHub\RaytSystem\client-7e85a8ba\windows\Start-RaytSystem.ps1" `
  -Mode Tunnel -LocalPort 8766 `
  -SshConfig "C:\Users\admin\Desktop\Project\ssh\config"
```

Открыть `http://127.0.0.1:8766/`. Остановка:

```powershell
& "$env:LOCALAPPDATA\TrafficHub\RaytSystem\client-7e85a8ba\windows\Stop-RaytSystem.ps1"
```

Launcher использует native Windows `ssh.exe`; WSL не требуется. Tunnel намеренно
зафиксирован на local port `8766`, поскольку loopback origin является частью
защитного контракта. Preview ищет
рабочий `py -3.12`, затем использует Python 3.12 из `uv`.

## Проверка и rollback

Проверить service, health, точные 10 пунктов меню, 8 систем, CSP/CSRF и создание
LOW_RISK workstream через Harness. Rollback —
переключить systemd unit на предыдущий immutable release SHA и повторить health.
Удалённый старый control center не восстанавливать как источник состояния.
