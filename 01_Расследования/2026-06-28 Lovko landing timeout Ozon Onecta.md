# 2026-06-28 Lovko landing timeout Ozon Onecta

## Симптом

- В live-логах Autolead появились ошибки:
  - `Ошибка Ozon [1]: Страница оффера не открылась: Page.goto: net::ERR_TIMED_OUT at https://vakansii-ozon.ru/...`
  - `Ошибка Onecta #2 [2]: Страница оффера не открылась: Page.goto: net::ERR_TIMED_OUT at https://onecta-rabota.ru/...`
- Ошибка похожа на сетевой сбой партнёрки, но проявляется на финальных Lovko landing-доменах, а не только на `tracking.lovko.pro`.

## Зона системы

- Autolead browser form-fill.
- `modules/vbiv_bot.py`.
- Lovko offer routing.
- Playwright proxy selection.

## Гипотеза

- Финальные landing-домены Lovko могут быть недоступны из server/browser contour без browser form proxy.
- Старый route detection знал про `tracking.lovko.pro`, `jobs-samokat.ru`, `logystpartner.ru` и Ozon по имени, но не покрывал все финальные Lovko landing-домены.

## Проверка

- Server repo: `/root/TrafficHub`, commit до фикса `786f38443`.
- Smoke внутри `traffichub_app`:
  - `https://vakansii-ozon.ru/...` без proxy таймаутит;
  - `https://vakansii-ozon.ru/...` через Playwright proxy открывается;
  - `https://onecta-rabota.ru/...` без proxy таймаутит;
  - `https://onecta-rabota.ru/...` через Playwright proxy открывается.
- После исправления и пересборки проверено для `admin`, `alex`, `artem`:
  - `_is_slow_lovko_route(...) == True`;
  - `page.goto(..., wait_until="domcontentloaded", timeout=65000)` открывает Ozon и Onecta через proxy.

## Наблюдение

- Это не ошибка конкретного пользователя.
- Причина в routing-контракте для Lovko final landing domains.
- Если у owner не включён browser form proxy, такие landing-домены могут продолжить таймаутить. Это ожидаемое поведение, потому что browser proxy используется только при включённом toggle.

## Вывод

- Финальные Lovko landing-домены нужно считать частью Lovko proxy/slow-route контура.
- Route detection должен работать по домену и названию оффера, а не только по `platform == "lovko"`.

## Исправление

- Product commit: `40df8b3cc fix: route lovko landing domains through proxy`.
- Добавлено:
  - `_is_lovko_proxy_landing_url()`;
  - slow-route detection для `vakansii-ozon.ru`, `onecta-rabota.ru`, `you-courier.ru`;
  - proxy routing для `vakansii-ozon.ru`, `onecta-rabota.ru`, `you-courier.ru`;
  - detection по offer names: `ozon`, `onecta`, `онекта`, `я еда`, `яндекс еда`.
- Regression test:
  - `tests/test_vbiv_bot_navigation.py::test_lovko_proxy_landing_domains_are_slow_routes`.

## Проверка после фикса

- GitHub checks для `40df8b3cc`: `CI` и `Build and Push Docker Image` зелёные.
- Live deploy: `autolead_bot` и `worker` пересобраны.
- `https://traffic-hub.pro/api/health` возвращает `status=ok`.
- Container tests: `18 passed`.
- Smoke внутри `traffichub_app`:
  - `admin`: Ozon и Onecta открываются через proxy;
  - `alex`: Ozon и Onecta открываются через proxy;
  - `artem`: Ozon и Onecta открываются через proxy;
  - `sergkuz2190`: proxy не включён, поэтому proxy-route не применяется.

## Следующий шаг

- Для новых пользователей, которым нужны Lovko landing-домены, включать browser form proxy:
  - `rabota_ru.proxy_enabled=True` + `rabota_ru.proxy_url`;
  - или `vbiv.form_proxy_enabled=True` + `vbiv.form_proxy_url`.
- Если снова появляется `Page.goto: net::ERR_TIMED_OUT` на Lovko landing:
  - сначала проверить `_playwright_proxy_from_config(owner_config)`;
  - затем проверить открытие final landing через Playwright proxy внутри `traffichub_app`.
