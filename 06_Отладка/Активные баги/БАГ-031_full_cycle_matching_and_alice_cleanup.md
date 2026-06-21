# БАГ-031: full-cycle sheets matching и мусорный owner alice

## Симптом

- В активных users появился `alice`, которого владелец проекта не создавал.
- У `alex` не матчились офферы из основной таблицы: строки были видны, но офферы не выбирались.
- `/login` на live падал 500 с `render_dashboard_index() missing 1 required positional argument: dashboard_dir`.

## Зона системы

- `control_license_users`, `users`, `tenant_memberships`, `control_user_app_configs`.
- `modules/vbiv_bot.py` — `_build_vacancy_title_by_id()`, matching по `vacancy_ids`/`vacancy_names`.
- `utils/runtime_store_pg_leads.py`, `utils/database.py` — owner-scoped `autolead_leads`.
- `api/server.py` — dashboard `/login`, `/index.html`.

## Гипотеза

- `alice` была тестовой/программной регистрацией, а не рабочим пользователем.
- Для строк из Sheets без `_raw_data` matching по `vacancy_ids` зависит от Rabota API titles. Если token отсутствует, нужно использовать уже собранные owner-scoped titles из PostgreSQL.
- У `alex` в настройках были чужие/admin `vacancy_id=54257329`, поэтому matching не мог сработать на его собственных строках.

## Проверка

- `alice` была найдена в `control_license_users` и `users`, создана `2026-06-20 21:58:56`, `client=alice`, `hwid=x`, runtime rows: `autolead_leads=0`, `autolead_send_history=0`, `autolead_retry_queue=0`.
- У `alex` фактические vacancy IDs в `autolead_leads`: `54272116`, `54283461`, `54287716`, `54288634`, `54290434`, `54291412`, `54292479`, `54295619`, `54304504`.
- До фикса у `alex` все 6 офферов ссылались на `54257329` и имели пустые `vacancy_names`.
- После фикса matching-аудит показал:
  - `admin`: 5/5 строк матчятся через DB title map `54257329 -> Оператор чата поддержки`;
  - `alex`: 168 строк матчятся на `Оператор текстовой поддержки маркетплейса`;
  - `artem`: 5/5 строк матчятся как broad offers;
  - `kursmerkusheva@gmail.com`: 213/213 строк матчятся через DB title map.
- Full pytest внутри контейнера после фикса: `295 passed, 43 skipped`.
- Live deploy: `autolead_bot` и `worker` пересозданы, `/api/health` OK, `/login` HTTP 200.

## Наблюдение

- `alice` удалена из `tenant_memberships`, `users`, `control_license_users`, `control_user_app_configs`, `control_user_app_auth`; backup сохранён на сервере `data/backups/alice_cleanup_20260621_121518.json`.
- `alex` owner-scoped config исправлен: офферы привязаны к `54272116`, `54283461` и `vacancy_names=[Оператор текстовой поддержки маркетплейса]`.
- Активная retry queue после проверок пустая.
- Safe full-cycle для `admin` завершился `ok`, `sent=0`, `skipped=1`, `errors=0`.
- Safe full-cycle для `alex` был остановлен вручную как тестовый зависший процесс; run `60` помечен `interrupted`, `sent=0`, `errors=0`.

## Вывод

- Root cause по matching: код зависел от Rabota API для получения titles по `vacancy_ids`, хотя для Sheets-only строк эти titles уже есть в owner-scoped PostgreSQL `autolead_leads`.
- Root cause по `alex`: owner config содержал чужой vacancy_id и пустой `vacancy_names`.
- Root cause по `/login`: два route вызывали `_render_dashboard_index()` без обязательного `DASHBOARD_DIR`.
- Полная цель ещё не закрыта: `kursmerkusheva@gmail.com` имеет 195 реальных телефонных строк на `Воксис`; боевой прогон будет создавать реальные отправки и должен выполняться отдельно под техработами с контролем логов и последующей очисткой тестовой истории.

## Следующий шаг

1. Проверить, почему full-cycle `alex` завис до безопасного завершения, не полагаясь на долгий сквозной run.
2. Для `kursmerkusheva@gmail.com` запускать controlled live-run только после явного ограничения объёма/наблюдения, потому что есть 195 телефонных строк.
3. После всех live-run очистить тестовые логи пользователей и отключить техработы только после проверки.
