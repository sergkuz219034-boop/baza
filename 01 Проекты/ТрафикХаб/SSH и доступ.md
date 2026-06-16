# SSH и доступ

## Канонический доступ

- Host: `150.241.70.31`
- Port: `22`
- User: `codex`
- Auth: `SSH key`

## Почему это важно

- локально человек и AI-агент запускают `ssh.exe` из разных Windows-контекстов;
- один и тот же private key-path ломался из-за ACL;
- следствие: нужен отдельный human path и отдельный agent path.

## Human path

- config: `C:\Users\sergk\OneDrive\Desktop\traffichubserver\ssh_access\config`
- команда:

```powershell
ssh -F C:\Users\sergk\OneDrive\Desktop\traffichubserver\ssh_access\config traffichub-codex
```

## Agent path

- config: `C:\Users\sergk\OneDrive\Desktop\traffichubserver\.codex_ssh\config`
- команда:

```powershell
ssh -F C:\Users\sergk\OneDrive\Desktop\traffichubserver\.codex_ssh\config traffichub-codex
```

## Минимальный smoke

```powershell
ssh -F C:\Users\sergk\OneDrive\Desktop\traffichubserver\.codex_ssh\config traffichub-codex "echo ok && whoami && hostname"
```

Ожидаемо:

- `ok`
- `codex`
- `TrafficHub.play2go.cloud`

## Риски

- `Permissions ... are too open` и `Load key ... Permission denied` обычно означают локальную ACL-проблему, а не проблему сервера;
- `root` не использовать как штатный вход;
- все project changes делать через `codex`, а host-level действия — через `codex + sudo`.
