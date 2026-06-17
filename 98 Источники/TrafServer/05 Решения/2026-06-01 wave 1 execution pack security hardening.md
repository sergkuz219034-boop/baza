# Wave 1 execution pack: security hardening

Дата: 2026-06-01

Связанные документы:
- [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
- [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)
- [2026-06-01 server-side ssh and proxy hardening plan.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20server-side%20ssh%20and%20proxy%20hardening%20plan.md)
- [2026-06-01 secret rotation priority plan.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20secret%20rotation%20priority%20plan.md)
- [2026-06-01 operational map current deployment.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20operational%20map%20current%20deployment.md)
- [2026-06-01 redacted secret inventory.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20redacted%20secret%20inventory.md)

## Анализ

Этот execution-pack покрывает `Wave 1`: security hardening перед любыми config/runtime изменениями.

Подтверждённые активные причины:

1. `Critical`:
- root SSH password auth
- secret sprawl в одном `.env`

2. `Low/Medium`, но operationally misleading:
- reverse proxy drift для `ACCOUNT_MANAGER_BASIC_AUTH_*`

Подтверждённые факты:

- live server допускает:
  - `PermitRootLogin yes`
  - `PasswordAuthentication yes`
- локальная текущая машина пока не владеет приватным ключом, уже разрешённым сервером
- один `.env` содержит несколько классов критичных секретов
- `ACCOUNT_MANAGER_BASIC_AUTH_*` заданы, но `Caddyfile` их не применяет

## Причина

### 1. Нельзя безопасно переходить к остальным волнам, оставив current SSH model

Пока сервер допускает `root + password`:
- любой следующий change window проходит под повышенным риском компрометации;
- lockout при hardening тоже остаётся возможным без подготовленного key-based доступа.

### 2. Secret sprawl увеличивает blast radius любой ошибки

Один `.env` сейчас связывает:
- auth
- perimeter
- partner integrations
- Telegram
- AI providers

Значит:
- даже локальная operational ошибка или утечка файла ударяет сразу по нескольким контурам.

### 3. Reverse proxy drift искажает реальную security posture

Если `ACCOUNT_MANAGER_BASIC_AUTH_*` выглядят “как включённая защита”, а в `Caddyfile` их нет:
- оператор может ошибиться в оценке периметра;
- тесты и incident response будут опираться на ложную модель.

## План исправления

### Шаг 1. SSH readiness без lockout

Цель:
- не выключать пароль раньше, чем появится подтверждённый вход по ключу

Порядок:

1. Подготовить публичный ключ, приватная часть которого реально есть на текущей машине.
2. Добавить его в `authorized_keys`.
3. Проверить новую отдельную сессию входа по ключу.
4. Только потом менять SSH policy.

### Шаг 2. SSH hardening

Цель:
- перевести сервер хотя бы в режим `root-by-key-only`, а затем желательно в `sudo-user + key`

Переходный безопасный вариант:

- `PermitRootLogin prohibit-password`
- `PasswordAuthentication no`

Целевой вариант:

- отдельный sudo-пользователь
- `PermitRootLogin no`
- `PasswordAuthentication no`

### Шаг 3. Critical secret rotation

Цель:
- ротировать auth/perimeter secrets отдельно от остальных классов

Порядок:

1. Подготовить новые значения заранее.
2. Сменить только критичный auth/perimeter класс.
3. Проверить:
- login
- token issuance/verification
- public domains

### Шаг 4. Reverse proxy truthfulness

Нужно принять одно из двух решений:

1. Либо реально включить `basic_auth` для `ACCOUNT_MANAGER_DOMAIN`
2. Либо удалить `ACCOUNT_MANAGER_BASIC_AUTH_*` как мёртвую конфигурацию

## Diff

### 1. SSH policy

Переходный безопасный diff:

```diff
# /etc/ssh/sshd_config
- PermitRootLogin yes
+ PermitRootLogin prohibit-password

- PasswordAuthentication yes
+ PasswordAuthentication no
```

```diff
# /etc/ssh/sshd_config.d/50-cloud-init.conf
- PasswordAuthentication yes
+ PasswordAuthentication no
```

Целевой diff:

```diff
# /etc/ssh/sshd_config
- PermitRootLogin prohibit-password
+ PermitRootLogin no
```

### 2. Caddy / AccountManager perimeter

Если perimeter auth нужен:

```diff
{$ACCOUNT_MANAGER_DOMAIN:am.traffic-hubcrm.ru} {
	encode zstd gzip

	basic_auth {
		{$ACCOUNT_MANAGER_BASIC_AUTH_USER} {$ACCOUNT_MANAGER_BASIC_AUTH_HASH}
	}

	reverse_proxy account_manager:8000 {
		header_down -Server
	}
	import security_headers
}
```

Если perimeter auth не нужен:

```diff
# docker-compose.yml
- ACCOUNT_MANAGER_BASIC_AUTH_USER=...
- ACCOUNT_MANAGER_BASIC_AUTH_HASH=...
```

### 3. Secret rotation

Точного diff по значениям здесь быть не должно.

Безопасный operational diff по подходу:

```diff
- rotate all secrets in one window
+ rotate Critical auth/perimeter secrets first, separately
```

## Почему это безопасно

1. SSH hardening делается только после подтверждения key-based входа.
2. Secret rotation разделена по blast radius, а не смешана в одну большую замену.
3. Proxy drift устраняется не “частично”, а переводится в честное состояние:
- либо защита реально есть,
- либо конфиг не притворяется, что она есть.

## Побочные эффекты

### Ожидаемые

- парольный вход перестанет работать
- часть старых скриптов на password auth перестанет работать, если их не адаптировать
- если включить `basic_auth` на `ACCOUNT_MANAGER_DOMAIN`, UX изменится

### Возможные скрытые

- automation/ops scripts могут оказаться завязаны на старую auth-модель
- при неудачной первой ротации auth secrets можно сломать login/token flows

## Проверка после исправления

### Обязательные проверки

1. Новая отдельная SSH-сессия по ключу реально работает.
2. `sshd -T` показывает:
- `passwordauthentication no`
- `pubkeyauthentication yes`
- `permitrootlogin prohibit-password` или `no`

3. Вход root по паролю больше не работает.
4. После первой волны ротации:
- логин работает
- токены выпускаются и валидируются
- public domains отвечают

5. По `ACCOUNT_MANAGER_DOMAIN` подтверждён один честный инвариант:
- либо `basic_auth` реально включён
- либо env/compose больше не создают ложного ожидания этой защиты

## Открытые вопросы

1. Нужен ли `AccountManager` вообще под отдельным `basic_auth` поверх существующего login-flow?
2. Есть ли ещё незафиксированные automation scripts, завязанные на password auth?
3. Есть ли product requirement держать root-доступ вообще, или уже можно сразу переходить на отдельного sudo-пользователя?
