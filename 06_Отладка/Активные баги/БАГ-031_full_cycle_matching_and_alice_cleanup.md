# БАГ-031: full-cycle sheets matching и мусорный owner alice

## Симптом

- В активных users появился `alice`, которого владелец проекта не создавал.
- У `alex` не матчились офферы из основной таблицы: строки были видны, но офферы не выбирались.
- `/login` на live падал 500 с `render_dashboard_index() missing 1 required positional argument: dashboard_dir`.
- После тестовых прогонов `alice` появилась повторно в live PostgreSQL.
- Строки основной таблицы с `Номер=нету` схлопывались дедупликацией в одну строку и не закрывались статусом.
- VkusVill (`leadsu/vkusvill`) периодически падал как `форма не подтверждена после отправки`; по debug HTML видимая форма оставляла `input[name="CITY"]` пустым.

## Зона системы

- `control_license_users`, `users`, `tenant_memberships`, `control_user_app_configs`.
- `modules/vbiv_bot.py` — `_build_vacancy_title_by_id()`, matching по `vacancy_ids`/`vacancy_names`.
- `utils/runtime_store_pg_leads.py`, `utils/database.py` — owner-scoped `autolead_leads`.
- `api/server.py` — dashboard `/login`, `/index.html`.
- `services/leads_service.py` — дедупликация перед `run_sender()`.
- `tests/conftest.py` — cleanup тестовых identities при pytest.
- `modules/sheets_sync.py` — запись статусов основной таблицы по `_sheet_row`.
- `modules/platforms/lovko.py` — заполнение формы VkusVill и закрепление hidden-полей города перед submit.

## Гипотеза

- `alice` была тестовой/программной регистрацией, а не рабочим пользователем.
- Для строк из Sheets без `_raw_data` matching по `vacancy_ids` зависит от Rabota API titles. Если token отсутствует, нужно использовать уже собранные owner-scoped titles из PostgreSQL.
- У `alex` в настройках были чужие/admin `vacancy_id=54257329`, поэтому matching не мог сработать на его собственных строках.
- Повторная `alice` создавалась не пользователем, а тестами, которые в контейнере видели live `DATABASE_URL`.
- Дедупликация считала `нету` реальным телефоном, поэтому сотни строк без телефона становились одним "дублем".
- У VkusVill JS сайта после клика по городу выставлял `REGION_ID/REGION_NAME`, но очищал hidden `CITY`; визуально город был `г. Москва`, а submit-валидация всё равно считала поле пустым.

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
- VkusVill debug HTML `2026-06-21`:
  - форма содержит `.js-request-city-input-name` со значением `г. Москва`;
  - `REGION_ID=3872`, `REGION_NAME=Москва и область`;
  - `input[name="CITY"]` оставался пустым и блок `.js-request-city-input` имел `_error` с текстом `Укажите город трудоустройства`.
- После фикса `modules/platforms/lovko.py`:
  - город выбирается только из `.js-request-city-items button.js-request-city-item`, а не из верхнего калькулятора страницы;
  - `CITY/REGION_ID/REGION_NAME/REGION_SUBDOMAIN` проставляются во все matching hidden inputs;
  - перед submit ставится lock на `input[name="CITY"]`, чтобы JS сайта не перезаписал значение пустотой;
  - пустой landing VkusVill возвращает `leadsu/vkusvill: landing пустой после повторной загрузки`, это transient и не permanent form-failure.
- Проверка VkusVill smoke на live для `alex`: один pending-лид `Вера Иванова`, оффер `ВкусВилл`, результат `sent=1`, `errors=0`, `Оффер ВкусВилл успешно заполнен!`.
- Full pytest в контейнере после фикса: `300 passed, 43 skipped`.
- Rebuilt-container targeted pytest после deploy: `38 passed`.
- Product commit/deploy: `4833afa15 fix: stabilize vkusvill form city submit`; `origin/main` совпал с server HEAD, `autolead_bot` и `worker` пересозданы, `/api/health` OK.
- Аудит пользователей после deploy:
  - `admin`: таблицы и service account есть, active offers `Воксис`, `Онекта`, pending `0`;
  - `artem`: таблицы и service account есть, active offers `Воксис`, `Онекта`, pending `0`;
  - `alex`: таблицы и service account есть, active offers `Дикси`, `X5`, `Воксис`, `Онекта`, `ВкусВилл`, `Onecta #2`, pending `409`, все с телефонами;
  - `kursmerkusheva@gmail.com`: таблицы и service account есть, active offers `Воксис`, pending `193`, все с телефонами;
  - `sergkuz2190`: не готов к full-cycle, нет таблиц/service account/offers.

## Наблюдение

- `alice` удалена из `tenant_memberships`, `users`, `control_license_users`, `control_user_app_configs`, `control_user_app_auth`; backup сохранён на сервере `data/backups/alice_cleanup_20260621_121518.json`.
- Повторная live-проверка `2026-06-27`: `users where lower(username)='alice' = 0`, `control_license_users where lower(login/client)='alice' = 0`.
- Повторная live-проверка `2026-06-30`: `alice` отсутствует в `users` и `control_license_users`.
- Дополнительно найден test leakage `test_user`: 1 строка в `control_user_app_configs` и 4 строки в `autolead_leads` без рабочего аккаунта.
- После commit `6a483516c` test cleanup покрывает `alice` и `test_user`, включая owner-scoped runtime tables.
- Live cleanup `2026-06-30`: `test_user` удалён из `control_user_app_configs` и `autolead_leads`, backup сохранён в `audit_test_identity_cleanup_20260630`.
- `alex` owner-scoped config исправлен: офферы привязаны к `54272116`, `54283461` и `vacancy_names=[Оператор текстовой поддержки маркетплейса]`.
- Активная retry queue после проверок пустая.
- Safe full-cycle для `admin` завершился `ok`, `sent=0`, `skipped=1`, `errors=0`.
- Safe full-cycle для `alex` был остановлен вручную как тестовый зависший процесс; run `60` помечен `interrupted`, `sent=0`, `errors=0`.
- Коммиты product repo:
  - `57f5ed37e` — `fix: prevent test identities and no-phone dedupe leaks`;
  - `e4aacfd0b` — `fix: use clear russian sheet log labels`;
  - `dd3a7e3bd` — `fix: treat blank leadsu landings as transient`;
  - `4833afa15` — `fix: stabilize vkusvill form city submit`.
- После `4833afa15` live `/api/health` OK, `autolead_bot` и `worker` healthy.
- GitHub remote `main` совпал с server HEAD `4833afa15`; checks с сервера не прочитаны, потому что `gh` не установлен.
- Повторная live-проверка `2026-06-27` после доменного/infra фикса:
  - `users`: `Artem`, `admin`, `alex`, `kursmerkusheva@gmail.com`, `sergkuz2190`; `alice` отсутствует;
  - `control_license_users`: те же 5 login без `alice`;
  - retry queue содержит 2 старые transient-записи Lovko timeout без успешной истории: `admin/Ozon` и `artem/Я еда`; они не удалены, чтобы не потерять повторную попытку по боевым лидам;
  - последние успешные full-cycle логи: `alex` завершился `sent=18 errors=0`, `kursmerkusheva@gmail.com` завершился `errors=0`.

## Вывод

- Root cause по matching: код зависел от Rabota API для получения titles по `vacancy_ids`, хотя для Sheets-only строк эти titles уже есть в owner-scoped PostgreSQL `autolead_leads`.
- Root cause по `alex`: owner config содержал чужой vacancy_id и пустой `vacancy_names`.
- Root cause по `/login`: два route вызывали `_render_dashboard_index()` без обязательного `DASHBOARD_DIR`.
- Root cause по повторной `alice`: pytest запускался внутри контейнера с live PostgreSQL `DATABASE_URL`; тестовая identity из auth/migration tests попадала в live tables. Защита: `tests/conftest.py` чистит known test identities до и после pytest.
- Root cause по no-phone строкам: placeholder `нету` участвовал в phone-dedupe как настоящий телефон. Исправление: dedupe применяется только к реальным телефонам, placeholders не считаются ключом.
- Пользовательский термин `pending` в логах заменён на "основная таблица"; `processed` описывается как "отработанная таблица".
- Root cause по VkusVill: автоматизация выбирала/синхронизировала не тот city-state. Страница имеет верхний калькулятор города и форму отклика; hidden `CITY` формы отклика очищался JS сайта перед submit. Исправление: выбор city item ограничен формой отклика, hidden city fields синхронизируются во всех формах и `CITY` защищается от очистки непосредственно перед submit.
- Массовая реальная отправка по `alex`/`kursmerkusheva@gmail.com` не запускалась: у них остались реальные строки с телефонами, такой прогон создаёт боевые заявки. Проверка выполнена controlled smoke.
- На `2026-06-27` подтверждено: баг с `alice` не воспроизводится, свежие run logs не показывают новых matching/no-phone/VkusVill regression. Оставшиеся retry-записи — старые transient Lovko timeouts, а не повторное создание `alice` и не permanent form-failure.
- На `2026-06-30` подтверждено: `alice` и `test_user` отсутствуют в live users/license/runtime хвостах. Retry queue пустая.

### Ссылки

- [[01 Расследования/2026-06-30 test_user cleanup leakage]]

## Следующий шаг

1. Не запускать массовую реальную отправку по `alex`/`kursmerkusheva@gmail.com` без контролируемого окна: у них остались только строки с телефонами.
2. Если нужен полный боевой прогон, запускать его под техработами и заранее согласовать объём, потому что это реальные заявки.
3. `sergkuz2190` нужно сначала донастроить: таблицы, service account, active offers.
