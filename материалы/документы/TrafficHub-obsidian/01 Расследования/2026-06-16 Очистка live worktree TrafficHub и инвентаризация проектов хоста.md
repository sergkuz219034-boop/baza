# 2026-06-16 Очистка live worktree TrafficHub и инвентаризация проектов хоста

## Симптом

- live `TrafficHub` на сервере был dirty;
- в repo root лежал посторонний `content-poster-bot`;
- не было короткой подтверждённой карты всех проектов хоста вокруг `TrafficHub`.

## Зона системы

- host `150.241.70.31`;
- `/root/TrafficHub`;
- соседние каталоги `/root/*`.

## Гипотеза

Если убрать грязные правки из live repo с backup перед cleanup и отдельно зафиксировать все server-side проекты, то:

- `TrafficHub` снова станет каноническим чистым mutable repo;
- будет ясно, какие сервисы относятся к продукту, а какие просто живут на том же хосте;
- дальнейшая wiki перестанет смешивать продуктовый код и соседние утилитарные проекты.

## Проверка

Подтверждено на live `2026-06-16`:

- до cleanup `git status --short` в `/root/TrafficHub` показывал:
  - `M AccountManager/dashboard/app.js`
  - `M AccountManager/dashboard/index.html`
  - `?? content-poster-bot/`
- перед cleanup сохранены backup-артефакты:
  - `/root/TrafficHub_backups/dirty_2026-06-16/accountmanager_dashboard.patch`
  - `/root/TrafficHub_backups/dirty_2026-06-16/content-poster-bot.tgz`
- после cleanup:
  - `content-poster-bot` вынесен в `/root/content-poster-bot`
  - правки dashboard сняты
  - `git status --short --branch` в `/root/TrafficHub` стал `## main...origin/main`
- доступный пользователю `codex` host contour:
  - `/root/TrafficHub` — git repo, читается
  - `/root/freellmapi` — git repo, читается, но `git` для `codex` упирается в `dubious ownership`
  - `/root/hermes-webui` — git repo, читается, но `git` для `codex` упирается в `dubious ownership`
  - `/root/hermes-workspace` — git repo, читается, но `git` для `codex` упирается в `dubious ownership`
  - `/root/hermes-user-bridge` — standalone python script directory
  - `/root/hermes-webui-auth` — standalone python auth proxy directory
  - `/root/mfo` — отдельный deployment directory с `docker-compose.yml`
  - `/root/content-poster-bot` — standalone python project вне `TrafficHub`
- текущий `TrafficHub` HEAD:
  - `a8f0be217fc7f23b8af6dead50b9968c9620cea1`

## Наблюдение

- грязь в `TrafficHub` была не архитектурной особенностью, а просто незавершённым локальным вмешательством в dashboard плюс случайно вложенным посторонним проектом;
- backup-контур на host уже используется и хранит несколько maintenance-срезов, не только этот cleanup;
- часть соседних git-репозиториев технически видна пользователю `codex`, но для `git`-операций требуется отдельная safe-directory или другой ownership path.

## Вывод

- канонический live repo `TrafficHub` снова clean;
- `content-poster-bot` нельзя считать частью `TrafficHub`, пока не появится явная интеграция в коде или compose;
- на хосте живёт несколько самостоятельных проектов, и wiki должна явно отделять product contour `TrafficHub` от host co-tenants.

## Следующий шаг

- обновить обзорные страницы `baza` и локальной wiki так, чтобы `TrafficHub` больше не считался dirty;
- зафиксировать server inventory как отдельный runtime-слой;
- если понадобится исследование соседних проектов, документировать их отдельно, не смешивая с картой `TrafficHub`.
