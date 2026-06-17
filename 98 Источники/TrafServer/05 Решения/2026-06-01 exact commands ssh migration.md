# Exact Commands: SSH Migration

Дата: 2026-06-01

## Анализ

На текущей машине уже есть всё, чтобы провести подготовку к безопасному SSH hardening:

- локальный ключ: `C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server`
- readiness helper: `C:\Users\Арт\Desktop\TrafServer\tools\ssh_key_readiness.py`
- локальный orchestration helper: `C:\Users\Арт\Desktop\TrafServer\tools\prepare_ssh_migration.ps1`
- OpenSSH client: `C:\Windows\System32\OpenSSH\ssh.exe`

Подтверждённое ограничение:

- текущий локальный ключ пока не совпадает с `server-side authorized_keys`;
- отключать password auth до добавления нового ключа нельзя.

## Причина

- Описание проблемы: hardening требует точной последовательности действий, иначе можно потерять доступ.
- Первопричина: на сервере разрешён password auth, а текущая машина ещё не доверена по ключу.
- Критичность: `High`
- Возможные последствия: lockout при ручной ошибке или пропуске шага.
- Рекомендуемое исправление: выполнять миграцию только поэтапно, с отдельной проверкой новой key-based сессии.

## План исправления

1. Проверить readiness локального ключа.
2. Ужесточить ACL у private key.
3. Добавить public key на сервер.
4. Проверить новый вход по ключу.
5. Только потом менять `sshd` policy.

## Diff

### 1. Локальная readiness-проверка

```powershell
& 'C:\Users\Арт\Desktop\TrafServer\tools\prepare_ssh_migration.ps1'
```

### 2. ACL hardening для локального private key

```powershell
$key = Join-Path $PWD '.ssh\sergey_server'
icacls $key /inheritance:r
icacls $key /remove *S-1-5-32-544 *S-1-5-18 'DESKTOP-E8GNASP\CodexSandboxUsers'
icacls $key /grant:r "$env:USERNAME:(F)"
```

### 3. Получить derived public key

```powershell
& 'C:\Users\Арт\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -c "import local_ssh; p=local_ssh.ensure_paramiko(); k=p.Ed25519Key.from_private_key_file(r'C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server'); print(f'{k.get_name()} {k.get_base64()} sergey_server')"
```

Ожидаемое значение:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE58kl6F5QOfas2Ih15Qvc/L81ElQHYAVXChv8ihtubc sergey_server
```

### 4. Добавить public key на сервер

Важно: дописать строку, а не перезаписать весь файл.

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE58kl6F5QOfas2Ih15Qvc/L81ElQHYAVXChv8ihtubc sergey_server
```

### 5. Проверить отдельную key-based сессию

```powershell
ssh -i "C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server" root@150.241.70.31
```

Успех:

- сессия открывается без password prompt;
- `whoami` возвращает `root`.

### 6. Только потом меняем SSH policy

```diff
# /etc/ssh/sshd_config
-PermitRootLogin yes
+PermitRootLogin prohibit-password

-PasswordAuthentication yes
+PasswordAuthentication no
```

```diff
# /etc/ssh/sshd_config.d/50-cloud-init.conf
-PasswordAuthentication yes
+PasswordAuthentication no
```

## Риски

- Самый высокий риск: менять `sshd` policy до проверки новой key-based сессии.
- Второй риск: случайно перезаписать `authorized_keys`.
- Третий риск: считать, что ключ “не работает”, когда на деле проблема только в ACL локального файла.

## Проверка после исправления

Нужно проверить:

1. `prepare_ssh_migration.ps1` больше не показывает проблемные ACL.
2. `ssh_key_readiness.py` показывает новый ключ и успешную server-side готовность.
3. Вход по ключу в новой сессии работает.
4. `sshd -T` показывает:
   - `passwordauthentication no`
   - `pubkeyauthentication yes`
   - `permitrootlogin prohibit-password` или `no`

## Дополнительные улучшения

- После стабилизации уйти с `root` на отдельного sudo-пользователя.
- Перевести локальные operational scripts с `TRAFSERVER_PASSWORD` на key-based auth.
- Вынести этот runbook в постоянный playbook доступа к прод-серверу.
