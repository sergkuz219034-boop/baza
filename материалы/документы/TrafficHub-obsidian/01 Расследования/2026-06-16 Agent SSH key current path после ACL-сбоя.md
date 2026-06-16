# 2026-06-16 Agent SSH key current path после ACL-сбоя

## Симптом

Codex shell не мог подключиться к серверу:

```text
Load key "C:\\Users\\sergk\\OneDrive\\Desktop\\traffichubserver\\.codex_ssh\\codex_login_ed25519": Permission denied
codex@150.241.70.31: Permission denied (publickey).
```

## Зона системы

- локальный Windows ACL;
- agent SSH profile `.codex_ssh/config`;
- серверный пользователь `codex@150.241.70.31`.

## Гипотеза

Файл `.codex_ssh/codex_login_ed25519` создан или защищён ACL другого Windows-контекста, поэтому текущий Codex-процесс не может его открыть.

## Проверка

- `ssh -F .codex_ssh/config traffichub-codex "echo ok && whoami && hostname"` падал до сетевого входа на чтении ключа;
- `Get-Acl .codex_ssh/codex_login_ed25519` вернул `Attempted to perform an unauthorized operation`;
- `icacls .codex_ssh/codex_login_ed25519` вернул `Access is denied`;
- исходный ключ `ssh_access/codex_login_ed25519.strict` читался текущим процессом.

## Наблюдение

Старый agent-key нельзя было починить из текущего процесса без смены владельца/админских действий. Рабочий путь:

1. создать новую копию `ssh_access/codex_login_ed25519.strict` в `.codex_ssh/codex_login_ed25519.current`;
2. отключить inheritance и выдать текущей учётке `Read`;
3. переключить `.codex_ssh/config` на `codex_login_ed25519.current`.

Smoke после правки:

```text
ok
codex
TrafficHub.play2go.cloud
```

## Вывод

Канонический agent-key для Codex desktop shell теперь `.codex_ssh/codex_login_ed25519.current`. Старый `.codex_ssh/codex_login_ed25519` считать устаревшим локальным артефактом с некорректным ACL.

## Следующий шаг

- При следующей чистке локальных SSH-файлов удалить или переименовать старый `.codex_ssh/codex_login_ed25519`, если процесс получит права на удаление.
- Не менять серверный `authorized_keys`: проблема была локальной.

