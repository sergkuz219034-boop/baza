# 2026-06-28 Lovko short tracking timeout Я еда

## Симптом

- В live-логах Autolead появляется ошибка:
  - `Ошибка Я еда [2]: Страница оффера не открылась: Page.goto: net::ERR_TIMED_OUT at https://tracking.lovko.pro/fik03d`
- Ошибка выглядит как проблема конкретного оффера, но потенциально затрагивает все короткие Lovko tracking-ссылки.

## Зона системы

- Autolead offer automation.
- `modules/vbiv_bot.py`.
- Lovko short tracking links: `tracking.lovko.pro/<short-code>`.
- Browser proxy для анкет.

## Гипотеза

- Возможные причины:
  - proxy не используется для Lovko;
  - proxy сохранён, но не применяется в Playwright;
  - `tracking.lovko.pro` или финальный landing недоступны из server/browser contour.

## Проверка

- Проверены owner configs через `utils.control_store`.
- Browser form proxy резолвится в Playwright proxy только если включён один из явных toggles:
  - `rabota_ru.proxy_enabled=True` + `rabota_ru.proxy_url`;
  - или `vbiv.form_proxy_enabled=True` + `vbiv.form_proxy_url`.
- После фикса `786f38443` сохранённый `rabota_ru.proxy_url` при `rabota_ru.proxy_enabled=False` не используется браузерными анкетами.
- Для users с включённым toggle Playwright proxy:
  - server: `http://217.29.62.68:8000`;
  - credentials присутствуют.
- `curl -I https://tracking.lovko.pro/fik03d` с сервера быстро возвращает `302 Location` на `https://you-courier.ru/vse-goroda-bn/...`.
- Chromium без preflight таймаутит на `https://tracking.lovko.pro/fik03d`.
- После server-side preflight и открытия финального URL через Playwright proxy страница открывается.

## Наблюдение

- Проблема не в отсутствии proxy.
- Проблема в том, что Chromium может зависать на коротком Lovko tracking URL до перехода по `302`.
- Финальный landing может требовать proxy: без proxy `you-courier.ru` из контейнера тоже таймаутит, через proxy открывается.
- При этом proxy не должен включаться только фактом сохранённого `proxy_url`; нужен включённый toggle.

## Вывод

- Для коротких Lovko tracking links нужен preflight: получить первый `Location` лёгким HTTP-запросом и передать браузеру финальный landing URL.
- Сам browser fill должен идти через Playwright proxy только при включённом proxy-toggle.

## Исправление

- Product commit: `c69420503 fix: preflight lovko short tracking redirects`.
- Product commit: `786f38443 fix: respect proxy toggle for browser forms`.
- Добавлено:
  - `_is_lovko_short_tracking_url()`;
  - `_resolve_lovko_tracking_redirect()`;
  - preflight в navigation loop для `platform == "lovko"`;
  - slow-route detection для `Я еда` / `Яндекс Еда`.
- Regression tests:
  - `tests/test_vbiv_bot_runtime_errors.py`;
  - `tests/test_vbiv_bot_navigation.py`;
  - `tests/test_proxy_config.py`.

## Проверка после фикса

- GitHub checks для `c69420503`: `CI` и `Build and Push Docker Image` зелёные.
- Live deploy: `autolead_bot` и `worker` пересобраны.
- `https://traffic-hub.pro/api/health` возвращает `status=ok`.
- Container tests: `14 passed`.
- Smoke:
  - `fik03d` резолвится в финальный `you-courier.ru` URL;
  - финальный URL открывается в Chromium через Playwright proxy при включённом toggle;
  - `maintenance_mode=False`.

## Следующий шаг

- Если Lovko short tracking снова даёт timeout, сначала проверять:
  - есть ли `302 Location` у tracking URL;
  - включён ли `rabota_ru.proxy_enabled` или `vbiv.form_proxy_enabled`;
  - открывается ли final landing через Playwright proxy, если proxy включён.
