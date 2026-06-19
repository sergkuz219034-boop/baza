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

## Вывод

Проблема была системной: sparse user-profile без fallback-наследования мог сделать "пустого" пользователя даже при живом backend и валидных owner bindings.

После фикса:

- owner-profile наследует рабочие operational defaults из базового конфига;
- пустые Google Sheets override-поля не должны затирать fallback без необходимости;
- проблема закрыта не только для `alex`, а для любого user со sparse profile.

## Следующий шаг

- при новых жалобах вида "ничего не работает" сначала проверять:
  - `offer_mapping`;
  - `rabota_ru.enable_responses / enable_autofit`;
  - `app_id/app_secret`;
  - owner-scoped `pending/processed` bindings;
- отдельно держать под наблюдением пользователей, у которых в cloud auth отсутствует `google_sa_json`: runtime может жить от уже сохранённого `service_account__<user>.json`, но это слабое место миграции.
