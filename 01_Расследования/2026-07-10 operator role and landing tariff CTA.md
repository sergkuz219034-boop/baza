# 2026-07-10 operator role and landing tariff CTA

## Симптом

Нужна отдельная роль `operator` с максимально ограниченным функционалом для рабочей обработки лидов. На публичном лендинге кнопки `Выбрать` в тарифах должны вести не в авторизацию, а в Telegram продавца.

Дополнение: Windows `LicenseKeygen.exe` / keygen должен уметь выпускать activation key с ролью `operator`, иначе новую роль нельзя выдать через локальный GUI-генератор.

## Зона системы

- `utils/access.py`
- `api/authz.py`
- `api/autolead_access.py`
- `api/routers/settings.py`
- `api/routers/offers.py`
- `api/routers/settings_maintenance.py`
- `api/routers/system.py`
- `traffic_hub/models/database.py`
- `traffic_hub/authz.py`
- `dashboard/app.js`
- `dashboard/index.html`
- `dashboard/landing.html`
- `tools/windows_launcher/LicenseKeygenLauncher.cs`
- `tools/activate_license.py`
- `.github/workflows/ci.yml`

## Гипотеза

Старый alias `operator = user` слишком широкий: оператор получает возможности обычного пользователя, включая настройки, офферы и запуск Autolead jobs. Для рабочего режима нужна отдельная роль ниже `user`.

## Проверка

- Код role-rank в `utils/access.py` проверен и изменён на `operator < user < admin`.
- PostgreSQL enum `userrole` на live расширен значением `operator`.
- Frontend проверен на hash-navigation и кнопки `data-user-action`.
- Live app/worker пересобраны из `/root/TrafficHub`.
- `/api/health` после deploy вернул `{"status":"ok"}`.
- Regression tests:
  - `tests/test_access.py`
  - `tests/test_auth_roles.py`
  - `tests/test_license_auth.py`
  - `tests/test_license_key_security.py`
  - `tests/test_traffic_tenant_isolation.py`
  - `tests/test_landing_routes.py`
  - `tests/test_settings_license_accounts.py`
  - `tests/test_settings_import_export.py`
  - `tests/test_offers_import_export.py`
  - `tests/test_jobs_router.py`
  - `tests/test_zarplata_router.py`
  - `tests/test_system_backups.py`
  - `tests/test_settings_maintenance.py`
  - `tests/test_autolead_access.py`
- Keygen/activation regression:
  - `tests/test_activate_license.py`
  - `tests/test_license_key_security.py`
- GitHub Actions 2026-07-10 подтвердил Windows compile job после добавления `LicenseKeygen.exe` в `.github/workflows/ci.yml`.

## Наблюдение

- `operator` больше не алиас `user`.
- `require_user` является порогом для изменения настроек, офферов, maintenance, system actions и jobs.
- `require_autolead_operator` используется как read/basic lead access threshold.
- UI скрывает user-level разделы и возвращает оператора на `#leads`, если запрещённая вкладка открыта прямым hash.
- Кнопки тарифов `Выбрать` на лендинге ведут на `https://t.me/sergkuz2190`.
- `tools/windows_launcher/LicenseKeygenLauncher.cs` теперь показывает роли `operator`, `user`, `admin`.
- `tools/activate_license.py::_normalize_role()` сохраняет `operator`, а не превращает его в `user`.
- CI компилирует `LicenseKeygen.exe`, чтобы C# regression был виден до релиза.

## Вывод

Роль `operator` стала отдельным минимальным рабочим режимом. Её нельзя снова маппить в `user`, иначе оператор получит доступ к настройкам и запуску jobs.

## Регрессия авторизации 2026-07-11

### Симптом

Короткий `TH3`-ключ, созданный `KEY.exe` с ролью `operator`, проходил проверку подписи, но `operator.traffic-hub.pro` показывал `Operator access could not be confirmed` и не открывал рабочее пространство.

### Проверка

- `tools/license_key_security.py::verify_activation_key()` корректно раскрывал `TH3` через `license_server` и возвращал payload с `role=operator`.
- В live-контейнере `utils/license.py::_normalize_license_role("operator")` возвращал `user`.
- `api/server.py::operator_login()` создавал пользователя и сессию, но `api/authz.py::set_session_principal()` повторно читал роль из PostgreSQL через `utils/license.py`; нормализация превращала её в `user`, поэтому frontend отклонял ответ.

### Исправление

- В `_ROLE_ALIASES` значения `operator` и `оператор` сохраняются как `_ROLE_OPERATOR`.
- Добавлен `tests/test_license_roles.py`, фиксирующий нормализацию для control store и PostgreSQL.
- Fallback-ошибки в `dashboard/operator.html` и ошибки формата/разрешения ключа в `tools/license_key_security.py` переведены на русский.
- Commit продукта: `7ca552f47` (`fix: restore operator key authorization`).

### Доказательство

- Точечные тесты: `16 passed`.
- GitHub CI и Docker build для `7ca552f47` завершились успешно.
- После recreate `traffichub_app` live `/api/health` вернул `status=ok`.
- Боевой smoke через последний серверный `TH3`-ключ вернул HTTP 200, `authenticated=true`, `role=operator`; последующий `/auth/session` вернул ту же роль.
- Тестовая учётная запись удалена, техработы после проверки выключены.

## Честная сводка оператора 2026-07-11

### Симптом

Стартовая сводка `operator.traffic-hub.pro` показывала статические демонстрационные значения кандидатов, вакансий, KPI, офферов и планов как будто это данные CRM.

### Решение

- Карточки приведены к рабочему порядку: `Новые кандидаты`, `Активные вакансии`, `KPI`, `Вознаграждение`.
- Демонстрационные числа заменены на `—`; подписи прямо сообщают, что данные или цель ещё не подключены.
- Для числовых значений добавлен `tabular-nums`, чтобы будущие реальные обновления не сдвигали интерфейс.
- Commit продукта: `042bea074` (`fix: remove fake operator dashboard metrics`).

### Проверка

- `tests/test_landing_routes.py`: `8 passed`.
- GitHub CI для commit завершился успешно.
- После recreate `traffichub_app` публичная страница содержит новые labels и `tabular-nums`, старые значения `184`, `82`, `27`, `14` отсутствуют.

## P0: захват аккаунта через регистрацию оператора 2026-07-11

### Симптом

`POST /auth/operator-login` мог создать операторский доступ небезопасно: ключ проверялся, но регистрация шла через путь, который мог перезаписать существующую учётную запись. В худшем сценарии владелец действующего ключа мог указать чужой логин, получить новый пароль и изменить роль/активность существующего пользователя.

### Зона системы

- `api/server.py::operator_login`
- `api/server.py::_apply_activate_license_key`
- `utils/control_store.py::create_user`
- `license_server/schema.sql::license_short_keys`
- `dashboard/operator.html`

### Проверка

- `api/server.py::_apply_activate_license_key` раньше использовал `control_store.upsert_user()`.
- `utils/control_store.upsert_user()` по `ON CONFLICT` обновляет существующего пользователя, включая hash пароля, роль и активность.
- Operator UI передаёт `name`, `telegram`, `activation_key`; логин оператора создаётся из `name` через `_transliterate_name()`.

### Исправление

- Только payload с `role=operator` допускается к операторскому входу.
- Operator form снова принимает `name` и `telegram`, но `username`, `password`, `role` и другие лишние поля запрещены через `extra="forbid"`.
- Login создаётся из `name`; password генерируется сервером после регистрации.
- Для создания пользователя добавлен `utils/control_store.create_user()`: только INSERT, без overwrite.
- Если login уже существует в `control_license_users` или `users`, регистрация возвращает `409`.
- Activation key помечается использованным атомарно в той же PostgreSQL-транзакции: `control_activation_keys_used.fingerprint` и `license_short_keys.used_at/used_by`.
- `license_server` сохраняет роль `operator`, а `license_short_keys` получил поля `used_at`, `used_by`.
- Commit продукта: `b2d3725a4` (`fix: prevent operator activation account takeover`).

### Доказательство

- `tests/test_operator_login_security.py` проверяет отказ `user`-ключу до активации, создание login из `name`, генерацию password и запрет privileged extra-полей.
- `tests/test_license_key_security.py` проверяет create-only activation, fingerprint/short-code claim и 409 при занятом login.
- Точечный набор: `22 passed`.
- Расширенный auth/license/access набор: `49 passed`.
- GitHub CI и Docker build для `b2d3725a4` завершились успешно.
- После recreate `traffichub_app` и `traffichub_license_server` live `/api/health` вернул `status=ok`.
- Deployed source внутри `traffichub_app` содержит `control_store.create_user`, `generated_password=True`, `_require_operator_key`; старый overwrite path через `_pg_update_user/_pg_set_role` в activation отсутствует.

## Следующий шаг

Если потребуется расширять операторский функционал, добавлять точечные permissions, а не повышать роль до `user`.

Для обновления downloadable/local keygen использовать Windows release/build контур: source уже поддерживает `operator`, но физический `.exe` должен быть пересобран из актуального коммита.

## Manager keygen 2026-07-16

### Наблюдение

- Роль `manager` уже поддерживалась каноническим source `tools/windows_launcher/LicenseKeygenLauncher.cs`, `license_server` и `POST /auth/manager-login`.
- На `manager.traffic-hub.pro` `operator_crm/app.js` выбирает только endpoint `/auth/manager-login`; operator-домен использует `/auth/operator-login`.
- Переданный дистрибутив `KEY.rar` содержал устаревший `KEY.exe`: в metadata была роль `operator`, но не `manager`.

### Исправление

`KEY.exe` пересобран из server-repo Windows C# compiler и заменён внутри `KEY.rar`. Проверка извлечённого нового exe подтвердила строки `manager` и `operator`. Исходный архив сохранён как `KEY.before-manager.rar` рядом с новым архивом.

## Visual refresh keygen 2026-07-16

`tools/windows_launcher/LicenseKeygenLauncher.cs` приведён к стилю Access Key Studio: тёмный studio-shell, верхняя status-панель, отдельные карточки параметров и результата, акцентная кнопка генерации. Подпись RSA, PIN-защита, short-key fallback и набор ролей не изменены.

Windows build выполнен `csc.exe`; обновлённый `KEY.exe` имеет SHA-256 `5f17e9eae89fdcaafdc687fcc811b417b0b731b4128acfbae25e47167e3f1670`. Этот же binary проверен внутри `Project/KEY.rar` и `Downloads/Telegram Desktop/KEY.rar`.

## Корректировка макета keygen 2026-07-16

### Симптом

Первый перенос стиля из `access-key-studio.html` затронул палитру, но не воспроизвёл композицию референса: заголовок накладывался на описание, а иконка, поле срока и карточки статуса отсутствовали.

### Проверка

- Сверен референс `access-key-studio.html` и фактический WinForms-код `tools/windows_launcher/LicenseKeygenLauncher.cs`.
- Подтверждено: текущий payload ключа содержит `login`, `client`, `password`, `role`, `issued_at` и опциональный `auth`, но не содержит даты истечения. Поэтому «30 дней» из демонстрационного HTML не является поддерживаемой функцией.

### Исправление

- В `KeygenForm` реализованы studio-shell, иконка, отдельные карточки параметров и результата, поле роли с русскими названиями, статусные карточки и исправленная вертикальная сетка без наложения текста.
- Срок показан честно как `Без ограничения`; он не создаёт фиктивного TTL.
- Роли `operator`, `manager`, `user`, `admin`, подпись RSA-SHA256, PIN, short-key API и безопасное сохранение уникального файла сохранены.

### Доказательство

- Product commit: `a6af00b96` (`style: align keygen with studio reference`).
- Нативная компиляция `csc.exe` успешна.
- SHA-256 бинарника: `b4de3e3758b09392115e3ff5fc1f2ae9858439305ace9ed8d8a4c2e55f297049`.
- Одинаковый hash подтверждён у двух `KEY.exe` и у exe, извлечённых из двух архивов `KEY.rar`.

### Ограничение / следующий шаг

Если нужен реальный выбор срока (30/90/180 дней), сначала нужно добавить и валидировать `expires_at` во всём контуре activation payload и серверной проверки; визуальную опцию нельзя включать отдельно.

### Исправление скругления 2026-07-16

Первый вариант рисовал только rounded-border через `Paint`; фон стандартного WinForms `Panel` оставался прямоугольным. В `KeygenForm` добавлен `ApplyRoundedRegion()`: он применяет `Region` по одному `GraphicsPath` к оболочке, карточкам, полям, кнопкам и status-блокам. Теперь скругление влияет и на границу, и на реально видимую поверхность. Commit продукта: `5d6ef15f6`.

### Коррекция отрисовки 2026-07-16

Проверка скриншотом показала, что `Region` нельзя применять к нативным `ComboBox` и `Button`: Windows частично отрезает их штатную отрисовку. Регион оставлен только на поверхностях-контейнерах, а границы карточек усилены, вынесены на 1 px внутрь и рисуются с `SmoothingMode.AntiAlias`. Контраст shell/card восстановлен. Commit продукта: `015c632de`.
