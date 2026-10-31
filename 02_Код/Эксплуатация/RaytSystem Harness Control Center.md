# RaytSystem Harness Control Center

С 2026-08-23 интерфейс управления Harness использует официальный web UI
RaytSystem Public OS, закреплённый на revision
`b5ac70560112758f78dd15852422ee697ac336f4`, с минимальным TrafficHub overlay.
Он является stateless UI и governed-command client; каноническими источниками
остаются Agent-OS, Codex, Graphify, Headroom, Caveman, Ponytail, CodeBurn и Wiki.

## Live

- текущий локальный server commit: `ceac9ac6a53a0637babdf3a77ecc94fbf674fdc2` (проверено 2026-10-08);
- service: `traffichub-raytsystem.service`;
- bind: только `127.0.0.1:8766`;
- health: `curl -fsS http://127.0.0.1:8766/healthz`;
- immutable release: `/opt/traffichub-raytsystem/ceac9ac6a53a0637babdf3a77ecc94fbf674fdc2`;
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

## Проверка gate — 2026-10-08

Bridge импортируется относительно immutable release панели, а не server repo,
переданного в `--root`. Новый release содержит актуальные bridge/server; прежний
`1d4e1e11ec9980029c63ba5dfaad6ad54d231d26` сохранён для rollback. Переключение:
`/etc/systemd/system/traffichub-raytsystem.service.d/10-harness-proof.conf`.
Обновлён только сервис RaytSystem, product containers и maintenance не менялись.

CLOSED перечитывает связанный proof manifest из `/root/TrafficHub`; отсутствующие
или изменённые файлы блокируют закрытие. Live HTTP: stale proof → 409, актуальный
proof → 202/CLOSED, replay → 202/replay, projection/health → 200. Product health
`https://traffic-hubcrm.ru/api/health` → 200. 34 целевых unittest PASS, py_compile
и diff check PASS. Полный product suite не запускался.

Rollback: удалить только созданный override `10-harness-proof.conf`, выполнить
`systemctl daemon-reload` и `systemctl restart traffichub-raytsystem.service`,
проверить `/healthz`. Прежний unit и release сохранены. Исторические CLOSED
записи не менялись; старым открытым задачам нужны bind и повторная проверка.

Доказательства: `C:/Users/admin/Desktop/Project/outputs/harness-fix-20261008/targeted-tests.txt`,
`release.json`, `live-smoke.json`; серверный backup
`/root/TrafficHub/data/backups/harness-fix-20261008/`.
