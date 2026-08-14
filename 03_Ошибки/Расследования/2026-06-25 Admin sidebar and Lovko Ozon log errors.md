# 2026-06-25 Admin sidebar and Lovko Ozon log errors

## Симптом

- В live UI `https://traffic-hubcrm.ru/#admin` под заголовком `Администрирование` не отображался username admin.
- В таблице `TrafficHub_Licenses` сохранялся риск внутреннего горизонтального/вертикального скролла вместо полноценной таблицы.
- В последних runtime-логах пользователей были повторяющиеся ошибки `alex/Ozon`: `Page.goto: net::ERR_TIMED_OUT` на `https://tracking.lovko.pro/click?pid=4126&offer_id=22`.

## Зона системы

- Frontend dashboard: `dashboard/index.html`, `dashboard/app.js`, `dashboard/style.css`.
- Autolead offer navigation: `modules/vbiv_bot.py`.
- Runtime logs: PostgreSQL table `autolead_app_log`.

## Гипотеза

- Username был добавлен в DOM, но оставался зависимым от HTML-атрибута `hidden`; при сбое/задержке применения `applyRoleUI()` строка оставалась скрытой.
- `Ozon` через Lovko является медленным tracking-route; после `net::ERR_TIMED_OUT` повтор на той же Playwright page может наследовать зависшее состояние Chromium.

## Проверка

- Проверен live repo `/root/TrafficHub`, HEAD до фикса: `57e2aa602`.
- Проверен container asset `/app/dashboard/index.html` и `/app/dashboard/app.js`: до rebuild внутри контейнера ещё был `hidden`.
- Проверены последние строки `autolead_app_log`:
  - `artem`: последние события без ошибок, полный цикл завершён;
  - `alex`: свежие ошибки только `Ozon` timeout, после части ошибок последующие заявки успешно заполнялись;
  - `kursmerkusheva@gmail.com`: последние найденные `Воксис/leadsu` ошибки старые, до текущего деплоя;
  - `sergkuz2190`: свежих ошибок в последних строках нет.

## Наблюдение

- Docker logs `traffichub_app` и `traffichub_worker` за последние часы не содержали новых critical traceback/error.
- Runtime app logs показывали, что проблема `alex/Ozon` не tenant-specific: это общий path Lovko/Ozon navigation.
- В `modules/vbiv_bot.py` уже была retry-навигация для slow Lovko route, но retry выполнялся на той же `page`.

## Вывод

- UI-регресс исправлен в общем dashboard-коде:
  - `sidebar-admin-username` больше не зависит от начального `hidden`;
  - видимость управляется через `data-admin-visible`;
  - admin table выводится как полноценная таблица без внутреннего скролла.
- Lovko/Ozon retry усилен в общем Autolead path:
  - slow Lovko/Ozon route получает 7 попыток;
  - navigation timeout увеличен до 65 секунд;
  - после timeout страница Playwright пересоздаётся в том же context.

## Следующий шаг

- Если `alex/Ozon` снова покажет `ERR_TIMED_OUT`, первый check: проверить доступность `tracking.lovko.pro` с сервера и через сохранённый form-fill proxy.
- Если проблема повторится только у одного owner, проверить его `target_url`, `proxy_url` и offer mapping, но кодовый retry уже общий для всех пользователей.

## Подтверждение

- Container tests: `pytest -q tests/test_dashboard_encoding.py tests/test_traffic_tenant_isolation.py` внутри `traffichub_app` — `9 passed`.
- Live `/api/health` после rebuild — `ok`.
- Container `/app` после rebuild содержит новый `sidebar-admin-username` без `hidden` и новый Lovko/Ozon retry comment.
- Product commit: `ce2366450 fix: stabilize admin sidebar and lovko navigation`.
- GitHub checks для `ce2366450`: `validate`, `windows-launcher`, `build-and-push` — success.
