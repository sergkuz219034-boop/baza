# Server-side SSH and Proxy Hardening Plan

Дата: 2026-06-01
Источник фактов:

- live server `150.241.70.31`
- `C:\Users\Арт\Desktop\TrafServer\remote_server_snapshot`

## Анализ

### SSH

Подтверждено на live server:

- `sshd -T` возвращает:
  - `permitrootlogin yes`
  - `pubkeyauthentication yes`
  - `passwordauthentication yes`
  - `kbdinteractiveauthentication no`

Подтверждено по конфигам:

- `/etc/ssh/sshd_config`
  - `PermitRootLogin yes`
  - `PasswordAuthentication yes`
  - `PubkeyAuthentication yes`
- `/etc/ssh/sshd_config.d/50-cloud-init.conf`
  - `PasswordAuthentication yes`

Вывод:

- password auth включён и в основном конфиге, и через cloud-init overlay;
- root login разрешён явно;
- проблема не гипотетическая и не сводится к “возможно default”.

### Текущая готовность к миграции без lockout

Подтверждено на live server:

- `/root/.ssh/authorized_keys` существует и содержит 2 ключа;
- `cloud-init` сейчас `disabled` через `/etc/cloud/cloud-init.disabled`;
- в `/etc/cloud/cloud.cfg.d/99-installer.cfg` исторически присутствует `ssh_pwauth: true`.

Подтверждено локально:

- в workspace есть приватный ключ `C:\Users\Арт\Desktop\TrafServer\.ssh\sergey_server`;
- его derived public key:
  - `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE58kl6F5QOfas2Ih15Qvc/L81ElQHYAVXChv8ihtubc derived-local-key`
- этот ключ **не совпадает** ни с одним ключом в текущем серверном `authorized_keys`.

Вывод:

- key-based auth на сервере уже поддерживается;
- но на текущей рабочей машине не найден приватный ключ, соответствующий уже разрешённым server-side ключам;
- отключать password auth прямо сейчас с этой машины небезопасно;
- сначала нужно добавить новый проверенный публичный ключ или найти приватный ключ к уже разрешённому серверному ключу.

### Reverse proxy drift

Подтверждено в snapshot:

- `docker-compose.yml`
  - объявлены `ACCOUNT_MANAGER_BASIC_AUTH_USER`
  - объявлены `ACCOUNT_MANAGER_BASIC_AUTH_HASH`
- `deploy/Caddyfile`
  - для `ACCOUNT_MANAGER_DOMAIN` отсутствует `basic_auth`
  - `basic_auth` используется только для `AI_AGENT_DOMAIN`

Вывод:

- конфигурация декларирует perimeter auth для Account Manager, но фактически не применяет её.

## Причина

### 1. Серверный SSH доступ через `root` + password auth

- Описание проблемы: сервер допускает прямой root login по паролю.
- Первопричина: явная insecure-настройка в `/etc/ssh/sshd_config` и поддержка password auth через `/etc/ssh/sshd_config.d/50-cloud-init.conf`.
- Критичность: `Critical`
- Возможные последствия:
  - brute-force и credential stuffing;
  - полный захват сервера при утечке пароля;
  - высокая чувствительность к ошибкам локального tooling и документации.
- Рекомендуемое исправление:
  - создать отдельного sudo-пользователя;
  - добавить SSH key auth;
  - переключить `PermitRootLogin no`;
  - переключить `PasswordAuthentication no`;
  - проверить cloud-init, чтобы он не вернул insecure state после reboot/reprovision.

### 2. Drift между compose и Caddy для Account Manager

- Описание проблемы: env vars для `ACCOUNT_MANAGER_BASIC_AUTH_*` существуют, но Caddy их не использует.
- Первопричина: конфигурация периметра разошлась с реальным proxy behavior.
- Критичность: `Low/Medium`
- Возможные последствия:
  - ложное чувство защищённости;
  - путаница в эксплуатации и расследованиях;
  - риск, что оператор считает perimeter auth включённым, хотя его нет.
- Рекомендуемое исправление:
  - либо реально включить `basic_auth` в `Caddyfile`;
  - либо удалить мёртвые env vars из compose и зафиксировать единственный реальный контур защиты.

## План исправления

### Вариант A. Предпочтительный для SSH

1. Подготовить публичный ключ, приватная часть которого реально есть у оператора на текущей машине.
2. Добавить этот ключ в `authorized_keys` для целевого пользователя.
3. Убедиться, что вход по ключу реально работает в новой отдельной сессии.
4. Создать отдельного пользователя, например `trafops`.
5. Добавить ему `authorized_keys`.
6. Проверить `sudo`-доступ.
7. После этого изменить SSH policy:
   - `PermitRootLogin no`
   - `PasswordAuthentication no`
8. Проверить `sshd -T`.
9. Перезапустить `ssh`.

### Вариант B. Минимальный временный

Если нельзя сразу уйти с root:

1. Сначала добавить рабочий публичный ключ, подтверждённый отдельной сессией.
2. Оставить `PubkeyAuthentication yes`.
3. Переключить:
   - `PermitRootLogin prohibit-password`
   - `PasswordAuthentication no`
4. Проверить, что root-вход возможен только по ключу.

## Diff

### SSH policy

Безопасный целевой diff:

```diff
# /etc/ssh/sshd_config
-PermitRootLogin yes
+PermitRootLogin no

-PasswordAuthentication yes
+PasswordAuthentication no

 PubkeyAuthentication yes
 KbdInteractiveAuthentication no
```

Если нужен промежуточный режим:

```diff
# /etc/ssh/sshd_config
-PermitRootLogin yes
+PermitRootLogin prohibit-password

-PasswordAuthentication yes
+PasswordAuthentication no
```

Для cloud-init overlay:

```diff
# /etc/ssh/sshd_config.d/50-cloud-init.conf
-PasswordAuthentication yes
+PasswordAuthentication no
```

### Caddy

Если хотим реально включить perimeter auth для Account Manager:

```diff
{$ACCOUNT_MANAGER_DOMAIN:am.traffic-hubcrm.ru} {
	encode zstd gzip

+	basic_auth {
+		{$ACCOUNT_MANAGER_BASIC_AUTH_USER} {$ACCOUNT_MANAGER_BASIC_AUTH_HASH}
+	}

	reverse_proxy account_manager:8000 {
		header_down -Server
	}
	import security_headers
}
```

Если perimeter auth не нужен, более честный diff такой:

```diff
# docker-compose.yml
-      - ACCOUNT_MANAGER_BASIC_AUTH_USER=${ACCOUNT_MANAGER_BASIC_AUTH_USER:-admin}
-      - ACCOUNT_MANAGER_BASIC_AUTH_HASH=${ACCOUNT_MANAGER_BASIC_AUTH_HASH:-}
```

## Риски

### SSH hardening

- На текущей рабочей машине не подтверждён приватный ключ, соответствующий уже разрешённым серверным ключам.
- Если отключить password auth до проверки key-based входа, можно потерять доступ к серверу.
- Если cloud-init управляет SSH policy, изменения могут откатиться после reprovision/reboot.
- Если automation/скрипты всё ещё завязаны на пароль, они перестанут работать.

### Caddy hardening

- Включение `basic_auth` поверх уже существующего login-flow может изменить UX и потребовать двойную аутентификацию.
- Удаление env vars без документации может сломать ожидания операторов.

## Проверка после исправления

### SSH

Проверить:

```text
sshd -T
```

Ожидаем:

- `permitrootlogin no` или `prohibit-password`
- `passwordauthentication no`
- `pubkeyauthentication yes`

Дополнительно:

- вход по ключу работает;
- вход root по паролю не работает;
- sudo-пользователь может выполнять operational задачи.
- текущая рабочая машина действительно владеет приватным ключом, который есть в server-side `authorized_keys`.

### Caddy

Проверить один из двух инвариантов:

- либо `ACCOUNT_MANAGER_DOMAIN` реально защищён `basic_auth`;
- либо compose/env больше не притворяется, что такая защита существует.

## Дополнительные улучшения

- Не хранить operational credentials в markdown/wiki вообще.
- Перевести локальные утилиты на SSH keys, а не только на env password.
- Добавить отдельный playbook для восстановления доступа, чтобы hardening не повышал операционный риск.
