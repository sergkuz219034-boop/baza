# БАГ-037: browser proxy применялся не ко всем офферам

## Симптом

- Статистика партнёрской сети показывает заполнение анкет с IP live-сервера, хотя proxy включён в настройках пользователя.
- Ошибка проявляется не как падение формы, а как неверный network-contour отправки.

## Зона системы

- `modules/vbiv_bot.py`
- `run_campaign()`
- Playwright browser launch для заполнения анкет
- user config: `rabota_ru.proxy_enabled/proxy_url` и `vbiv.form_proxy_enabled/form_proxy_url`

## Гипотеза

- Proxy из настроек создаётся корректно, но применяется только для части офферов.

## Проверка

- Live code `modules/vbiv_bot.py` на commit `39e72fa2b`:
  - `_playwright_proxy_from_config(config_data)` возвращал `form_proxy`;
  - вложенный `_should_use_form_proxy(platform_key, offer_name, target_url)` разрешал proxy только для `lovko`, известных Lovko-hosts и списка названий офферов.
- Runtime config check через `docker compose exec -T autolead_bot` подтвердил, что у части пользователей proxy-контур включён без вывода секретов.

## Наблюдение

- Новые домены, новые платформы или офферы вне allowlist стартовали Chromium без proxy.
- В этом случае ПП видела IP сервера, а не IP proxy.

## Вывод

- Allowlist доменов для browser proxy был неверной границей. Если пользователь включил proxy и `_playwright_proxy_from_config()` вернул рабочий proxy, он должен применяться ко всем Playwright-анкетам.

## Исправление

- Product commit: `9b1dc68eb fix: apply form proxy to all browser offers`.
- `_should_use_form_proxy(form_proxy)` вынесен в top-level helper и теперь возвращает `bool(form_proxy)`.
- Вложенный allowlist в `run_campaign()` удалён.
- `run_campaign()` передаёт proxy во все browser launches при включённом proxy-контуре.

## Проверка после фикса

- `pytest -q`: `435 passed, 43 skipped`.
- GitHub checks на `9b1dc68eb`: `CI` и `Build and Push Docker Image` зелёные.
- Live deploy: `docker compose up -d --build autolead_bot worker`.
- `/api/health`: `ok`.
- `autolead_bot` и `worker`: healthy.
- Runtime helper в контейнере:
  - `_should_use_form_proxy({"server": "http://127.0.0.1:8080"}) == True`;
  - `_should_use_form_proxy(None) == False`.

## Следующий шаг

- Если ПП всё ещё показывает неверный IP, проверять уже не routing-code, а работоспособность самого proxy: внешний IP из Chromium внутри `traffichub_app`, auth proxy, geo proxy и правила партнёрской сети.
