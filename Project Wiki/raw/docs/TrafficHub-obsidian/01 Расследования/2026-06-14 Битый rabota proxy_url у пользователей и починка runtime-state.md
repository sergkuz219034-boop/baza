# 2026-06-14 Битый rabota proxy_url у пользователей и починка runtime-state

## Симптом

- У `Artem` и `ARTEM2` Autolead не открывал формы через browser-runner.
- При принудительном включении proxy browser получал:
  - `net::ERR_PROXY_CONNECTION_FAILED`
- Часть офферов без proxy уходила в:
  - `chrome-error://chromewebdata/`
  - timeout до конечного лендинга.

## Зона системы

- Live runtime:
  - `/root/TrafficHub/modules/vbiv_bot.py`
  - `utils.control_store.load_user_config(...)`
  - owner-scoped user config в live control store
- Settings API:
  - `/root/TrafficHub/api/routers/settings.py`
- Пользователи:
  - `Artem`
  - `ARTEM2`
  - эталон рабочего proxy:
    - `admin`
    - `alex`

## Гипотеза

- Проблема была не в самих офферах, а в том, что у части пользователей в `rabota_ru.proxy_url` лежал мусор вместо реального proxy URL.
- Из-за этого browser-runner поднимал невалидный proxy route и ломал redirect ещё до формы.

## Проверка

- По live control store подтверждено:
  - `admin`
    - `rabota_proxy_enabled=False`
    - `rabota_proxy_url` валиден, нормализуется как `http://<user>:<pass>@217.29.62.68:8000`
  - `alex`
    - `rabota_proxy_enabled=True`
    - `rabota_proxy_url` валиден, тот же host/port `217.29.62.68:8000`
  - `Artem`
    - `rabota_proxy_url` был строкой `Artem`
  - `ARTEM2`
    - `rabota_proxy_url` был строкой `Artem`
- При тесте с их сохранённым state и `proxy_enabled=True`:
  - `Artem / Воксис` → `ERR_PROXY_CONNECTION_FAILED`
  - `Artem / Онекта` → `ERR_PROXY_CONNECTION_FAILED`
  - `ARTEM2 / Самокат` → `ERR_PROXY_CONNECTION_FAILED`
  - `ARTEM2 / Воксис` → `ERR_PROXY_CONNECTION_FAILED`
  - `ARTEM2 / Дикси` → `ERR_PROXY_CONNECTION_FAILED`
  - `ARTEM2 / X5` → `ERR_PROXY_CONNECTION_FAILED`
- После подстановки в память рабочего proxy от `admin`:
  - `Artem / Воксис` → `voxys-rabota.ru`, форма открывается
  - `Artem / Онекта` → `rabotadoma.site`, форма открывается
  - `ARTEM2 / Самокат` → `logystpartner.ru`, лендинг открывается
  - `ARTEM2 / Воксис` → `voxys-rabota.ru`, форма открывается
  - `ARTEM2 / X5` → `x5-dostavka.ru`, лендинг/форма открываются
- Выполнена безопасная server-side починка текущего runtime-state через `control_store.save_user_config(...)`:
  - `Artem.rabota_ru.proxy_enabled=True`
  - `Artem.rabota_ru.proxy_url=<рабочий proxy admin>`
  - `ARTEM2.rabota_ru.proxy_enabled=True`
  - `ARTEM2.rabota_ru.proxy_url=<рабочий proxy admin>`
- После сохранения в live control store без подмены в памяти подтверждено:
  - `Artem / Воксис` → `PASS`, `voxys-rabota.ru`
  - `Artem / Онекта` → `PASS`, `rabotadoma.site`
  - `ARTEM2 / Воксис` → `PASS`, `voxys-rabota.ru`
  - `ARTEM2 / X5` → `PASS`, `x5-dostavka.ru`
  - `ARTEM2 / Дикси` → `PASS`, `anketa-dixy.ru`
  - `alex / Ozon` → `PASS`, `vakansii-ozon.ru`
- В live code внесена постоянная защита:
  - `/root/TrafficHub/api/routers/settings.py`
    - `_normalize_proxy_url()` теперь отклоняет мусорные значения вроде `Artem` с `HTTP 400`
  - `/root/TrafficHub/modules/vbiv_bot.py`
    - `_playwright_proxy_from_config()` больше не строит proxy из невалидного мусора;
    - пишет короткое предупреждение в лог и возвращает `None`
  - добавлены server-side тесты:
    - `/root/TrafficHub/tests/test_proxy_config.py`
- После пересборки `autolead_bot` и `worker` подтверждено:
  - `autolead_server_bot` healthy
  - `traffichub_worker` healthy
- Дополнительный live-fix в `/root/TrafficHub/modules/vbiv_bot.py`:
  - timeout открытия страницы больше не помечает оффер как permanently blocked на весь текущий запуск;
  - для медленных `lovko/samokat` redirect-цепочек увеличены:
    - `max_nav_attempts`
    - `nav_timeout`
    - пауза между retry
- Повторный live smoke `5/5` на прокси после rebuild:
  - `ARTEM2 / X5` → `5/5`, конечный URL `x5-dostavka.ru`
  - `alex / Ozon` → `5/5`, конечный URL `vakansii-ozon.ru`
- Повторная проверка form-readiness на прокси подтвердила:
  - `alex / Ozon`
    - `visibleInputs=7`
    - `hasName=true`
    - `hasPhone=true`
    - `hasCity=true`
    - `hasSubmit=true`
  - `ARTEM2 / X5`
    - `visibleInputs=7`
    - `hasName=true`
    - `hasPhone=true`
    - `hasCity=true`
    - `hasSubmit=true`
  - `ARTEM2 / Самокат`
    - лендинг/форма открываются;
    - `visibleInputs=7`
    - `hasName=true`
    - `hasPhone=true`
    - `hasCity=true`
    - `hasSubmit=true`
  - `Artem / Воксис`
    - отдельный повторный smoke `5/5`
    - `voxys-rabota.ru`
    - `inputs=7`
    - форма видима
  - `Artem / Онекта`
    - `rabotadoma.site`
    - `visibleInputs=5`
    - `hasName=true`
    - `hasPhone=true`
    - `hasCity=true`
    - `hasSubmit=true`
- Остаточные ограничения после починки proxy-state и code hardening:
  - `ARTEM2 / Самокат`
    - не мёртвый, но flaky по redirect-path:
      - ранний smoke `3/5`
      - после nav-fix отдельный повторный smoke дал:
        - `attempt=1` → `ERR_TIMED_OUT`
        - `attempt=2..5` → `logystpartner.ru`
    - следствие:
      - upstream остаётся медленным;
      - но runtime больше не должен преждевременно выбрасывать оффер из всего цикла после первого timeout
  - `ARTEM2 / Я еда`
    - `disabled.html`
  - `ARTEM2 / Четыре лапы`
    - `disabled.html`
  - `ARTEM2 / ВкусВилл`
    - больше не уходит в `vpn-detected`
    - открывает `vkusvill.ru/job/...`
    - route стабилен `5/5`
    - это отдельная нестандартная форма `VkusvillLeadsuPlatform`; простая DOM-эвристика не доказывает end-to-end submit

## Наблюдение

- Корень сегодняшней поломки `Autolead с выставленным proxy` был в данных, а не в форме:
  - у `Artem` и `ARTEM2` в runtime лежал битый `proxy_url`.
- Подмена на валидный proxy сразу оживила большинство проблемных офферов.
- После этого внесена уже не временная, а постоянная защита в код:
  - мусорный `proxy_url` больше нельзя штатно сохранить через settings API;
  - browser-runner больше не должен поднимать заведомо сломанный proxy config из legacy-мусора.
- Значит:
  - proxy для browser-runner в принципе рабочий;
  - текущий host `217.29.62.68:8000` пригоден для `Onecta`, `Voxys`, `Ozon`, `X5`, `Дикси`, `ВкусВилл`;
  - `Самокат` на этом же proxy частично рабочий, но нестабилен по upstream redirect.

## Вывод

- Починка выполнена на двух уровнях:
  - runtime-state:
    - `Artem` и `ARTEM2` переведены на валидный proxy в live control store
  - live code:
    - settings API валидирует proxy format
    - browser-runner безопасно игнорирует невалидный proxy
- После этого `Autolead` с proxy подтверждённо рабочий по открытию формы:
  - `Artem`: `Воксис`, `Онекта`
  - `ARTEM2`: `Воксис`, `X5`, `Дикси`, `ВкусВилл`
  - `alex`: `Ozon`
- Неполностью закрытые кейсы:
  - `ARTEM2 / Самокат` остаётся flaky на upstream redirect-path;
  - `ARTEM2 / Я еда` и `ARTEM2 / Четыре лапы` отключены upstream;
  - для `ВкусВилл` подтверждён рабочий route до формы, но не проводилась отдельная test-submit в production.

## Следующий шаг

- Если нужен operational green-state по всем офферам:
  - отдельно разбирать flaky-цепочку `ARTEM2 / Самокат`
  - не считать `Я еда` и `Четыре лапы` багом кода, пока upstream отдаёт `disabled.html`
  - при работе с `ВкусВилл` проверять именно `VkusvillLeadsuPlatform`, а не только generic DOM smoke
