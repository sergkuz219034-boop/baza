# Operational Runbook: Key-Based SSH Migration

Дата: 2026-06-01
Контекст: live server `150.241.70.31`, текущая рабочая машина `C:\Users\Арт\Desktop\TrafServer`

## Анализ

Текущее состояние подтверждено:

- сервер принимает:
  - `PermitRootLogin yes`
  - `PasswordAuthentication yes`
  - `PubkeyAuthentication yes`
- на сервере уже есть `/root/.ssh/authorized_keys` с 2 ключами;
- на текущей машине есть локальный приватный ключ:
  - `C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server`
- derived public key этого ключа:
  - `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE58kl6F5QOfas2Ih15Qvc/L81ElQHYAVXChv8ihtubc sergey_server`
- этот ключ не совпадает с текущими server-side ключами:
  - `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII6Z374+3guOSQKm9TbR93PGVuqSaZakcH4WpPapskpg traffichub-server`
  - `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICss9TxZU4odhV763AC6FF/f0oJ2GUKxLTW5CpKHLcvd sergk@TrafficHub`
- локально доступен OpenSSH client:
  - `C:\Windows\System32\OpenSSH\ssh.exe`

Вывод:

- переход на key-based auth возможен;
- но отключать password auth до добавления нового рабочего ключа нельзя.

## Причина

### Проблема

Сервер уже поддерживает SSH-ключи, но текущая рабочая машина не владеет приватным ключом, который уже доверен сервером.

### Первопричина

Операционная среда клиента и server-side `authorized_keys` не синхронизированы.

### Критичность

`High`

### Последствия

- lockout при преждевременном отключении password auth;
- невозможность безопасно завершить hardening за один шаг;
- зависимость от известного root-пароля сохраняется дольше, чем нужно.

### Рекомендуемое исправление

Сначала добавить новый публичный ключ, приватная часть которого есть на текущей машине, и только после успешной проверки отключать password auth.

## План исправления

1. Нормализовать права локального приватного ключа.
2. Вывести/сохранить публичный ключ от текущего приватного ключа.
3. Добавить этот публичный ключ на сервер в `/root/.ssh/authorized_keys`.
4. Открыть вторую отдельную сессию и проверить вход по ключу.
5. Только после успешного входа по ключу менять SSH policy.
6. После смены policy ещё раз проверить новый вход.

## Diff

### Этап 1. Подготовить локальный ключ

Если `ssh.exe` ругается на “UNPROTECTED PRIVATE KEY FILE”, нужно ужесточить ACL локального файла `sergey_server`.

Безопасная цель:

```text
У файла приватного ключа должны остаться права только у текущего пользователя.
```

Подтверждённый текущий симптом на этой машине:

- у `C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server` слишком широкие ACL;
- `ssh.exe` уже выдавал предупреждение `UNPROTECTED PRIVATE KEY FILE`.

Быстрая локальная диагностика:

```text
C:\Users\Арт\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe C:\Users\Арт\Desktop\TrafServer\tools\ssh_key_readiness.py
```

Этот helper:

- печатает ACL ключа;
- выводит derived public key;
- если задан `TRAFSERVER_PASSWORD`, сравнивает его с server-side `/root/.ssh/authorized_keys`.

Точный локальный набор команд для ACL hardening:

```powershell
$key = Join-Path $PWD '.ssh\sergey_server'
icacls $key /inheritance:r
icacls $key /remove *S-1-5-32-544 *S-1-5-18 'DESKTOP-E8GNASP\CodexSandboxUsers'
icacls $key /grant:r "$env:USERNAME:(F)"
```

Цель проверки после этого:

```powershell
icacls 'C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server'
```

Нежелательно оставлять у ключа `Modify` или `Full` для посторонних групп/пользователей.

### Этап 2. Публичный ключ для добавления на сервер

Проверенный derived public key текущей машины:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE58kl6F5QOfas2Ih15Qvc/L81ElQHYAVXChv8ihtubc sergey_server
```

### Этап 3. Добавить ключ на сервер

Безопасное изменение server-side `authorized_keys`:

```diff
# /root/.ssh/authorized_keys
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE58kl6F5QOfas2Ih15Qvc/L81ElQHYAVXChv8ihtubc sergey_server
```

Важно:

- не удалять существующие 2 ключа до тех пор, пока новый ключ не проверен;
- не заменять файл целиком, а именно дописать новую строку.

### Этап 4. Проверить вход по ключу

Целевой тест:

```text
ssh -i C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server root@150.241.70.31
```

Успехом считается:

- отдельная новая сессия логинится без password prompt;
- на сервере видно `whoami -> root`.

### Этап 5. Только потом сменить SSH policy

Предпочтительный промежуточный diff:

```diff
# /etc/ssh/sshd_config
-PermitRootLogin yes
+PermitRootLogin prohibit-password

-PasswordAuthentication yes
+PasswordAuthentication no
```

И overlay:

```diff
# /etc/ssh/sshd_config.d/50-cloud-init.conf
-PasswordAuthentication yes
+PasswordAuthentication no
```

Если после этого всё стабильно, финальная версия:

```diff
# /etc/ssh/sshd_config
-PermitRootLogin prohibit-password
+PermitRootLogin no
```

## Риски

### Высокий риск

- если отключить `PasswordAuthentication` до успешной проверки нового ключа, можно потерять доступ;
- если случайно перезаписать `authorized_keys`, можно удалить существующие рабочие ключи.

### Средний риск

- локальный OpenSSH может продолжать отвергать ключ при слишком широких ACL;
- часть automation всё ещё может быть завязана на пароль.

## Проверка после исправления

Минимальный набор проверок:

1. Новая отдельная SSH-сессия входит по ключу.
2. `sshd -T` показывает:
   - `pubkeyauthentication yes`
   - `passwordauthentication no`
   - `permitrootlogin prohibit-password` или `no`
3. Логин root по паролю больше не работает.
4. Существующие operational действия всё ещё выполняются.

## Дополнительные улучшения

- после стабилизации лучше уйти от `root` к отдельному sudo-пользователю;
- локальные operational scripts потом стоит перевести с `TRAFSERVER_PASSWORD` на key-based auth;
- желательно хранить публичный ключ рядом с runbook, а приватный ключ — вне wiki и без широких ACL.
