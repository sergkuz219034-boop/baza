# 5-Command SSH Checklist

Дата: 2026-06-01
Цель: безопасно перейти от `root + password` к проверенному key-based доступу без lockout.

## Анализ

Что уже подтверждено:

- сервер всё ещё принимает `root` по паролю;
- текущий локальный ключ пока не находится в `server-side authorized_keys`;
- локальный private key имеет слишком широкие ACL;
- отключать `PasswordAuthentication` до проверки нового key-based входа нельзя.

## Причина

- Описание проблемы: SSH hardening здесь опасен, если делать его “в лоб”.
- Первопричина: нет подтверждённого рабочего key-based доступа именно с текущей машины.
- Критичность: `High`
- Возможные последствия: потеря доступа к серверу.
- Рекомендуемое исправление: выполнять только в правильной последовательности.

## План исправления

1. Проверить readiness.
2. Ужесточить ACL локального private key.
3. Снова проверить readiness.
4. Добавить public key на сервер.
5. Проверить новый вход по ключу.

## Diff

### Команда 1. Посмотреть readiness

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Арт\Desktop\TrafServer\tools\prepare_ssh_migration.ps1"
```

### Команда 2. Исправить ACL у private key

```powershell
$key = "C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server"; icacls $key /inheritance:r; icacls $key /remove *S-1-5-32-544 *S-1-5-18 "DESKTOP-E8GNASP\CodexSandboxUsers"; icacls $key /grant:r "$env:USERNAME:(F)"
```

### Команда 3. Повторно проверить readiness и увидеть derived public key

```powershell
$env:TRAFSERVER_PASSWORD='cryptO2190$'; & "C:\Users\Арт\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "C:\Users\Арт\Desktop\TrafServer\tools\ssh_key_readiness.py"
```

Ожидаемый смысл результата:

- ACL уже без лишних групп;
- появится строка с public key;
- пока ещё будет `NO MATCH`, если ключ не добавлен на сервер.

### Команда 4. Добавить public key на сервер

```powershell
$pub = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE58kl6F5QOfas2Ih15Qvc/L81ElQHYAVXChv8ihtubc sergey_server'; $env:TRAFSERVER_PASSWORD='cryptO2190$'; & "C:\Users\Арт\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "C:\Users\Арт\Desktop\TrafServer\tools\remote_exec.py" "printf '%s\n' '$pub' | sudo tee -a /root/.ssh/authorized_keys >/dev/null && sudo chmod 600 /root/.ssh/authorized_keys && sudo tail -n 3 /root/.ssh/authorized_keys"
```

Важно:

- эта команда **дописывает** ключ;
- она не должна заменять весь `authorized_keys`.

### Команда 5. Проверить новый вход по ключу

```powershell
ssh -i "C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server" root@150.241.70.31
```

После успешного входа уже можно переходить к изменению:

```text
PermitRootLogin prohibit-password
PasswordAuthentication no
```

## Риски

- Самый высокий риск: менять SSH policy до команды 5.
- Второй риск: ошибочно переписать `authorized_keys` вместо дописывания.
- Третий риск: считать проблему серверной, когда ключ просто отвергается из-за ACL локального файла.

## Проверка после исправления

После выполнения команд:

1. Команда 5 должна открывать новую SSH-сессию без password prompt.
2. `ssh_key_readiness.py` должен перестать показывать `NO MATCH`.
3. Только после этого имеет смысл трогать `sshd_config`.

## Дополнительные улучшения

- После стабилизации перейти с `root` на отдельного sudo-пользователя.
- Потом перевести локальные утилиты с `TRAFSERVER_PASSWORD` на чистый key-based режим.
