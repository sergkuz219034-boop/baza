# БАГ-006 Настройки в dashboard выглядели слетевшими, admin-auth снова был битым

## Симптом
И `admin`, и обычный `user` в dashboard видели пустые или сброшенные настройки. Дополнительно `admin` больше не проходил `validate_user(...)`.

## Зона системы
- `api/routers/settings.py` — endpoint `GET /api/settings`.
- `dashboard/app.js` — `loadSettings()` ожидает payload `editable/readonly/api_tokens`.
- `utils.license` — проверка и обновление пароля `admin`.
- PostgreSQL `control_user_app_configs`, `control_user_app_auth` — канонические per-user настройки и auth-secrets.

## Гипотеза
Проблема не в потере данных, а в web/API-контуре:

- frontend открывает `GET /api/settings`;
- если route отсутствует или отдаёт не тот payload, форма выглядит как будто настройки пропали;
- параллельно `admin` мог не входить из-за drift bcrypt hash.

## Проверка
- В live PostgreSQL `control_user_app_configs` записи пользователей сохранились, включая `admin` и `artem`.
- Внутри `autolead_server_bot` `load_config(force_reload=True)` возвращал корректные user-scoped конфиги:
  - `admin` — `6` офферов;
  - `artem` — `2` оффера.
- Runtime cache `/app/data/runtime/secrets/config.json` выглядел как shared/mixed cache и не мог считаться каноном.
- `validate_user("admin", "cryptR2!90$")` до правки возвращал `False`.

## Наблюдение
Канонические данные не были потеряны. Сломан был слой доступа к ним:

- dashboard зависел от `GET /api/settings`;
- `admin` login drift дополнительно маскировал проблему и мешал верификации через обычный UI-flow.

## Вывод
Первопричина двойная:

- в `settings`-router отсутствовал/выпал `GET /api/settings`, которого ждал frontend;
- live auth hash `admin` снова разошёлся с ожидаемым паролем.

## Решение
- В `api/routers/settings.py` возвращён `GET /api/settings`, который отдаёт:
  - `editable`
  - `readonly`
  - `api_tokens`
- Для `user` endpoint режет payload до `OPERATOR_EDITABLE_KEYS`, для `admin` отдаёт полный editable-набор.
- На live password `admin` переустановлен и снова проходит `validate_user("admin", "cryptR2!90$")`.
- Добавлен регрессионный тест `test_settings_get_returns_user_scoped_payload`.

## Проверка после фикса
- `POST https://traffic-hubcrm.ru/auth/login` под `admin` -> `200`.
- `GET https://traffic-hubcrm.ru/api/settings` с session cookie -> `200`.
- Live payload содержит ожидаемые поля:
  - `editable.daily_goal = 500`
  - `api_tokens.app_id = 865`
- `pytest -q tests/test_auth_roles.py -q` внутри `autolead_server_bot` -> `5 passed`.

## Следующий шаг
- При любом симптоме “слетели настройки” сначала различать:
  - потерю данных в PostgreSQL `control_user_app_configs`;
  - поломку `GET /api/settings`;
  - drift пароля/сессии, из-за которого frontend вообще не может получить payload.
