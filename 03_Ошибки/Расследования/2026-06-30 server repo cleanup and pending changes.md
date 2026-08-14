# 2026-06-30 server repo cleanup and pending changes

## Симптом

В `/root/TrafficHub` накопился грязный worktree: незакоммиченные изменения одновременно в `AccountManager`, `Zarplata`, `Leads.su`, runtime-store invites и frontend.

## Зона системы

- server repo `/root/TrafficHub`
- `AccountManager/*`
- `dashboard/*`
- `api/routers/settings.py`
- `api/routers/settings_core.py`
- `modules/platforms/leadsu.py`
- `modules/zarplata_api.py`
- `services/leads_service.py`
- `utils/database.py`
- `utils/runtime_store_pg_invites.py`

## Гипотеза

- Часть diff была реальной функциональной работой, а не мусором.
- Дополнительно worktree был раздут CRLF drift в нескольких `AccountManager` файлах.
- Если просто «почистить» repo revert-ом, можно потерять уже нужные live-правки.

## Проверка

- На live host снят `git status --short` и `git diff --numstat`.
- Подтверждено 17 осмысленных файлов изменений после нормализации LF:
  - `AccountManager` UI/Telegram profile handling;
  - `Zarplata auto invite`;
  - `Leads.su` form recovery;
  - invite history storage;
  - мелкие dashboard/settings updates.
- Прогнаны релевантные проверки:
  - `python -m py_compile` по backend-файлам;
  - `pytest` по наборам `Leadsu`, `AccountManager access/import/content`, `settings`, `database/invite`.
- Результат:
  - `40 passed` на первых двух наборах;
  - `23 passed, 38 skipped` на `database/invite/account_manager content`.
- Server repo зафиксирован commit `daa91c12e` (`Finalize pending AccountManager and Zarplata changes`) и успешно запушен.
- После этого в `main` появился следующий commit `fa98fd964` (`Wire Zarplata auto invites into sender`) с родителем `daa91c12e`.
- GitHub Actions для обоих workflow на `daa91c12e` зелёные:
  - `CI`
  - `Build and Push Docker Image`
- К моменту финальной проверки `/root/TrafficHub` уже clean на `fa98fd964`.
- Для `AccountManager` выявлен отдельный Docker build hang. Runtime-применение сделано контролируемым hotfix-путём:
  - файлы из `/root/TrafficHub/AccountManager/*` скопированы в `traffichub_account_manager:/app/...`;
  - контейнер перезапущен;
  - health стал `healthy`;
  - внутри `/app/dashboard/index.html` подтверждён переход `TrafficHub -> https://traffic-hub.pro`.

## Наблюдение

- Основная проблема была не в «мусорном repo», а в незавершённом накопленном наборе рабочих изменений.
- CRLF drift действительно мешал читать diff и создавал ложный шум.
- `AccountManager` build path через Docker в момент проверки оказался нестабильным, но git/push/checks и runtime hotfix позволили не оставлять live в старом состоянии.

## Вывод

Server repo приведён в clean state без потери pending-функционала:

- код зафиксирован и pushed;
- checks зелёные;
- live runtime подтянут;
- `AccountManager` ссылка `TrafficHub` теперь ведёт на primary domain `traffic-hub.pro`;
- source of truth для текущего server repo — clean `HEAD fa98fd964`.

## Следующий шаг

- Отдельно разобрать, почему `docker compose build account_manager` / `docker buildx` зависает на host, чтобы следующий deploy не требовал runtime `docker cp` hotfix.
