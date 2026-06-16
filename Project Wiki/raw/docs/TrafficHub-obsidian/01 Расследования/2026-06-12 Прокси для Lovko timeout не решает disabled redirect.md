## Симптом

> Обновление от 13.06.2026:
> в этом расследовании была подтверждена внешняя проблема `disabled.html`, но тогда ещё не была найдена внутренняя ошибка parser proxy в `modules/vbiv_bot.py`.
> См. [[2026-06-13 Ozon Lovko proxy parser bug и disabled upstream]].

- В логах Autolead по офферу Lovko/Ozon появлялся таймаут:
  - `Page.goto: net::ERR_TIMED_OUT at https://tracking.lovko.pro/click?pid=41266&offer_id=22`

## Зона системы

- Live runtime `autolead_server_bot`
- Browser flow офферов в `modules/vbiv_bot.py`
- Proxy config `rabota_ru.proxy_enabled` / `rabota_ru.proxy_url`

## Гипотеза

- Если включить HTTP-прокси для `rabota_ru`, Playwright-сценарий Lovko перестанет падать по network timeout и сможет открыть оффер.

## Проверка

- Локально подтверждено по коду:
  - `artifacts/live_fix/modules/vbiv_bot.py:76`:
    - `_playwright_proxy_from_config(config_data)` берёт proxy из `rabota_ru.proxy_url`
  - `artifacts/remote_edit/modules/rabota_api.py:65`:
    - тот же proxy используется и для Rabota API
- На live server для пользователя `admin` временно установлен:
  - `rabota_ru.proxy_enabled=true`
  - `rabota_ru.proxy_url=http://uE0D08:LZCcvM@217.29.62.68:8000`
- Выполнены live проверки внутри контейнера `autolead_server_bot`:
  - `curl -I -L -x http://uE0D08:LZCcvM@217.29.62.68:8000 https://tracking.lovko.pro/click?pid=41266&offer_id=22`
  - Playwright `page.goto(..., wait_until="domcontentloaded")` с тем же proxy

## Наблюдение

- HTTP chain через proxy:
  - первый ответ приходит быстро;
  - `tracking.lovko.pro` отдаёт `302` на `http://tracking.lovko.pro/disabled.html`
- Playwright runtime:
  - `RESP_STATUS=200`
  - `FINAL_URL=https://tracking.lovko.pro/disabled.html`
  - `TITLE=Disabled`
  - `BODY=Disabled`

## Вывод

- Данный proxy не решает проблему Lovko.
- Он убирает исходный timeout на первом переходе, но вместо рабочего оффера переводит трафик на `disabled.html`.
- Следствие:
  - проблема не сводится к простой сетевой недоступности без proxy;
  - текущий proxy либо заблокирован у партнёрки/Lovko, либо ведёт в нежелательный антифрод/disabled маршрут.

## Следующий шаг

- Не считать `217.29.62.68:8000` рабочим решением для Lovko/Ozon.
- Проверить другой residential/mobile proxy или прямую причину блокировки у Lovko.
- Если proxy оставлять в продукте, нужен отдельный runtime-check:
  - после `page.goto` валидировать, что `page.url` не содержит `disabled.html`;
  - при `disabled.html` логировать прикладную ошибку партнёрки, а не generic timeout.
