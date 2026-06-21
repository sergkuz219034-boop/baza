# БАГ-031: full-cycle sheets matching и мусорный owner alice

## Симптом

- В активных users появился `alice`, которого владелец проекта не создавал.
- У `alex` не матчились офферы из основной таблицы: строки были видны, но офферы не выбирались.
- `/login` на live падал 500 с `render_dashboard_index() missing 1 required positional argument: dashboard_dir`.
- После тестовых прогонов `alice` появилась повторно в live PostgreSQL.
- Строки основной таблицы с `Номер=нету` схлопывались дедупликацией в одну строку и не закрывались статусом.

## Зона системы

- `control_license_users`, `users`, `tenant_memberships`, `control_user_app_configs`.
- `modules/vbiv_bot.py` — `_build_vacancy_title_by_id()`, matching по `vacancy_ids`/`vacancy_names`.
- `utils/runtime_store_pg_leads.py`, `utils/database.py` — owner-scoped `autolead_leads`.
- `api/server.py` — dashboard `/login`, `/index.html`.
- `services/leads_service.py` — дедупликация перед `run_sender()`.
- `tests/conftest.py` — cleanup тестовых identities при pytest.
- `modules/sheets_sync.py` — запись статусов основной таблицы по `_sheet_row`.

## Гипотеза

- `alice` была тестовой/программной регистрацией, а не рабочим пользователем.
- Для строк из Sheets без `_raw_data` matching по `vacancy_ids` зависит от Rabota API titles. Если token отсутствует, нужно использовать уже собранные owner-scoped titles из PostgreSQL.
- У `alex` в настройках были чужие/admin `vacancy_id=54257329`, поэтому matching не мог сработать на его собственных строках.
- Повторная `alice` создавалась не пользователем, а тестами, которые в контейнере видели live `DATABASE_URL`.
- Дедупликация считала `нету` реальным телефоном, поэтому сотни строк без телефона становились одним "дублем".

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
- Повторная проверка `alice` `2026-06-21`:
  - до cleanup: `users.id=14`, `control_license_users.login=alice`, `client=alice`, `hwid=x`, tenant `personal-alice`;
  - после cleanup: `users=0`, `control_license_users=0`, `tenants=0`, `tenant_memberships=0`, `control_user_app_configs=0`.
- После фикса `tests/conftest.py` targeted pytest по auth/migrations: `6 passed`, после теста `alice=0`.
- Полный pytest после фикса: `296 passed, 43 skipped`, после теста `alice=0`.
- Dry-run дедупликации no-phone после deploy:
  - `admin`: 4/4 строк без телефона дошли до campaign path;
  - `artem`: 4/4 строк без телефона дошли до campaign path до закрытия общей admin/artem таблицы;
  - `alex`: 254/254 строк без телефона дошли до campaign path;
  - `kursmerkusheva@gmail.com`: 18/18 строк без телефона дошли до campaign path.
- Safe no-phone status update без реальной отправки форм:
  - `admin`: 4 строки помечены `Нет номера`;
  - `alex`: 254 строки помечены `Нет номера`;
  - `kursmerkusheva@gmail.com`: 18 строк помечены `Нет номера`;
  - `artem`: 0 строк осталось, потому что использует ту же основную таблицу, что `admin`.
- Проверка остатков после no-phone update:
  - `admin`: `pending_total=0`;
  - `artem`: `pending_total=0`;
  - `alex`: `pending_total=412`, все с телефоном;
  - `kursmerkusheva@gmail.com`: `pending_total=195`, все с телефоном;
  - `sergkuz2190`: runtime не готов, нет настроенных таблиц/service account.

## Наблюдение

- `alice` удалена из `tenant_memberships`, `users`, `control_license_users`, `control_user_app_configs`, `control_user_app_auth`; backup сохранён на сервере `data/backups/alice_cleanup_20260621_121518.json`.
- `alex` owner-scoped config исправлен: офферы привязаны к `54272116`, `54283461` и `vacancy_names=[Оператор текстовой поддержки маркетплейса]`.
- Активная retry queue после проверок пустая.
- Safe full-cycle для `admin` завершился `ok`, `sent=0`, `skipped=1`, `errors=0`.
- Safe full-cycle для `alex` был остановлен вручную как тестовый зависший процесс; run `60` помечен `interrupted`, `sent=0`, `errors=0`.
- Коммиты product repo:
  - `57f5ed37e` — `fix: prevent test identities and no-phone dedupe leaks`;
  - `e4aacfd0b` — `fix: use clear russian sheet log labels`.
- После `e4aacfd0b` live `/api/health` OK, `autolead_bot` и `worker` healthy.
- GitHub remote `main` совпал с server HEAD `e4aacfd0b`; checks с сервера не прочитаны, потому что `gh` не установлен.

## Вывод

- Root cause по matching: код зависел от Rabota API для получения titles по `vacancy_ids`, хотя для Sheets-only строк эти titles уже есть в owner-scoped PostgreSQL `autolead_leads`.
- Root cause по `alex`: owner config содержал чужой vacancy_id и пустой `vacancy_names`.
- Root cause по `/login`: два route вызывали `_render_dashboard_index()` без обязательного `DASHBOARD_DIR`.
- Root cause по повторной `alice`: pytest запускался внутри контейнера с live PostgreSQL `DATABASE_URL`; тестовая identity из auth/migration tests попадала в live tables. Защита: `tests/conftest.py` чистит known test identities до и после pytest.
- Root cause по no-phone строкам: placeholder `нету` участвовал в phone-dedupe как настоящий телефон. Исправление: dedupe применяется только к реальным телефонам, placeholders не считаются ключом.
- Пользовательский термин `pending` в логах заменён на "основная таблица"; `processed` описывается как "отработанная таблица".
- Полная цель ещё не закрыта: `kursmerkusheva@gmail.com` имеет 195 реальных телефонных строк на `Воксис`; боевой прогон будет создавать реальные отправки и должен выполняться отдельно под техработами с контролем логов и последующей очисткой тестовой истории.

## Следующий шаг

1. Не запускать массовую реальную отправку по `alex`/`kursmerkusheva@gmail.com` без контролируемого окна: у них остались только строки с телефонами.
2. Проверить боевую отправку на ограниченном объёме через `admin`/`artem`, как разрешённый smoke-контур.
3. После всех live-run очистить тестовые логи пользователей и отключить техработы только после проверки.
