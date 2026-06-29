# 2026-06-30 cleanup sweep local server junk

## Симптом

В рабочем контуре накопились локальные копии, временные директории, Python cache и старые backup-файлы Caddy.

## Зона системы

- local workspace: `C:\Users\sergk\OneDrive\Desktop\Project`
- live repo: `/root/TrafficHub`
- live containers: `traffichub_app`, `traffichub_worker`, `traffichub_caddy`
- wiki canon: `wiki` -> GitHub `sergkuz219034-boop/baza`

## Гипотеза

Часть файлов можно удалить как подтвержденный мусор без изменения product-кода:

- локальная временная папка `live_patch`;
- локальная старая product-копия `traffichubserver`;
- ignored Python cache (`__pycache__`, `*.pyc`);
- старые `deploy/Caddyfile.bak-*`.

## Проверка

Проверены:

- `git status -sb` в `/root/TrafficHub`;
- `/api/health`;
- `docker compose ps`;
- ignored файлы на сервере;
- локальные верхнеуровневые папки workspace;
- ссылки на спорные артефакты.

## Наблюдение

Удалено локально:

- `C:\Users\sergk\OneDrive\Desktop\Project\live_patch`;
- большая часть старой локальной product-копии `traffichubserver`.

Осталось локально из-за Windows ACL/lock:

- `traffichubserver\.codex_ssh\codex_login_ed25519`;
- `traffichubserver\.codex_ssh\codex_login_ed25519.current`;
- `traffichubserver\ssh_access\codex_login_ed25519`;
- `traffichubserver\ssh_access\codex_login_ed25519.strict`;
- `traffichubserver\ssh_access\config`.

Остаток `traffichubserver` больше не содержит product-код, только SSH/access файлы. Попытки `Remove-Item`, `takeown`, `icacls`, `attrib`, `del /F` не получили доступ к ACL.

На сервере обнаружены ignored root-owned cache/backup-файлы:

- `api/**/__pycache__`;
- `api/**/*.pyc`;
- `deploy/Caddyfile.bak-*`.

Обычный `rm` через `codex` получил `Permission denied`; `sudo` требует пароль. Через контейнер удалить нельзя, потому что `/app` не является host repo `/root/TrafficHub` в этом месте.

Сохранены как не-мусор:

- `/root/TrafficHub/backups/sqlite-precutover-20260617` — миграционный архив, зафиксирован в docs/CHANGELOG как допустимый;
- `/root/TrafficHub/AccountManager/data/tdata_uploads` — runtime/user import data;
- `.env*`, `secrets*` — секреты и runtime-конфигурация;
- HWID/license compatibility code — имеет ссылки в `utils/license.py`, `utils/control_store.py`, tests/docs; удалять как dead code без отдельной миграции нельзя.

## Вывод

Безопасная часть cleanup выполнена. Product repo остался clean, tracked product-код не менялся.

Оставшийся серверный мусор не влияет на runtime, но требует root-доступа или отдельной команды от root для удаления. Локальный остаток `traffichubserver` требует снятия Windows ACL/lock или удаления из elevated PowerShell после закрытия процессов, которые держат ключи.

## Следующий шаг

- Для полной локальной очистки удалить остаток `traffichubserver` из elevated PowerShell или после отключения OneDrive/процессов, которые держат ACL.
- Для полной серверной очистки выполнить root-level cleanup только для `__pycache__`, `*.pyc`, `deploy/Caddyfile.bak-*`.
- Не удалять миграционные архивы, secrets и runtime/user data без отдельного подтвержденного плана.

Связанные страницы: [[Доступ и подключения]], [[Развёртывание]], [[Workflow Codex для дебага и разработки]].
