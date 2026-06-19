# БАГ-019: sparse user-profile терял рабочие operational defaults

## Симптом

У отдельных пользователей, в частности `alex`, live-контур выглядел как "ничего не работает":

- `offer_mapping` пустой;
- `rabota_ru.enable_responses = false`;
- `rabota_ru.enable_autofit = false`;
- `app_id/app_secret` не доходили до runtime-конфига;
- `full cycle` завершался с нулевой статистикой без явной ошибки.

## Зона системы

- `services/leads_service.py`
- `utils.control_store`
- owner-scoped user profiles в `control_user_app_configs`
- `load_config(force_reload=True)` внутри owner-context

## Гипотеза

Пользовательский профиль мог храниться в sparse-форме: только часть Google Sheets bindings и минимум UI-полей. Если runtime при загрузке такого профиля не наследует рабочие fallback defaults из базового конфига, пользователь получает формально валидный, но практически пустой operational contour.

## Проверка

- Live `alex` profile в `control_store` содержал:
  - пустой `offer_mapping`;
  - `enable_responses=false`, `enable_autofit=false`, `include_invites=false`;
  - свои `pending/processed` spreadsheet IDs;
  - рабочий `rabota_access_token` уже существовал в cloud auth.
- В `services/leads_service.py` до фикса:
  - `_load_user_config_profile(username, fallback)` вызывал
    `_deep_merge_dicts(_new_user_profile_template({}), profile)`
  - затем вызывал
    `_apply_profile_operational_defaults(profile, {})`
  - то есть вместо реального fallback-конфига передавался пустой словарь.
- Из-за этого sparse profile не донаследовал operational defaults из базового live-конфига.

## Наблюдение

Root cause был не только в данных `alex`, а в общем code path загрузки owner-profile.

Фикс в `TrafficHub` commit `75d82c5`:

- `_load_user_config_profile()` теперь строит template от реального `fallback`;
- `_apply_profile_operational_defaults()` теперь получает реальный `fallback`;
- дополнительно вызывается `_strip_empty_google_sheet_overrides(profile, fallback)`.

Точечный runtime-ремонт `alex` выполнен отдельно:

- восстановлен рабочий owner-profile на базе действующего контура;
- сохранены его собственные `pending/processed` Google Sheets bindings.

После deploy и restart:

- `alex` снова грузит `offer_mapping = 6`;
- `enable_responses = true`;
- `enable_autofit = true`;
- `include_invites = true`;
- `app_id/app_secret` присутствуют в runtime;
- его owner-scoped pending/processed bindings сохранены.

Повторная live-проверка 2026-06-19 показала второй системный дефект того же слоя:

- часть user-profile могла хранить чужой `autolead_owner_username` или вообще не хранить его;
- sparse profile исправлялся в runtime только частично, но не пересохранялся обратно в `control_user_app_configs`;
- из-за этого старые или повреждённые owner-scoped профили могли снова всплывать после следующих сохранений и reload.

Дополнительный фикс в `TrafficHub` commit `d3dee1a`:

- добавлен `_normalize_user_profile_identity(profile, username)`;
- `_load_user_config_profile()` теперь принудительно нормализует `autolead_owner_username` под текущего пользователя;
- после merge/default/self-heal профиль пересохраняется обратно в `control_user_app_configs`, если runtime его исправил;
- это делает repair постоянным для текущих и будущих пользователей, а не только для текущего процесса.

Live-верификация после deploy `d3dee1a`:

- `docker exec autolead_server_bot pytest -q tests/test_config_merge.py tests/test_leads_service_sheets_flow.py tests/test_sheets_queues.py tests/test_vbiv_offer_matching.py`
- результат: `35 passed`
- active user profiles в `control_store` после forced reload:
  - `admin -> owner=admin`
  - `alex -> owner=alex`
  - `artem -> owner=artem`
  - `kursmerkusheva@gmail.com -> owner=kursmerkusheva@gmail.com`
  - `dev -> owner отсутствует, pending/processed sheets не заданы, operational contour не настроен`

## Вывод

Проблема была системной: sparse user-profile без fallback-наследования мог сделать "пустого" пользователя даже при живом backend и валидных owner bindings.

После фикса:

- owner-profile наследует рабочие operational defaults из базового конфига;
- пустые Google Sheets override-поля не должны затирать fallback без необходимости;
- owner identity в user-profile самовосстанавливается и записывается обратно в `control_store`;
- проблема закрыта не только для `alex`, а для любого текущего и будущего user со sparse profile, если у него вообще есть валидно заведённый owner-scoped контур.

## Следующий шаг

- при новых жалобах вида "ничего не работает" сначала проверять:
  - `offer_mapping`;
  - `rabota_ru.enable_responses / enable_autofit`;
  - `app_id/app_secret`;
  - owner-scoped `pending/processed` bindings;
- отдельно держать под наблюдением пользователей, у которых в cloud auth отсутствует `google_sa_json`: runtime может жить от уже сохранённого `service_account__<user>.json`, но это слабое место миграции.
