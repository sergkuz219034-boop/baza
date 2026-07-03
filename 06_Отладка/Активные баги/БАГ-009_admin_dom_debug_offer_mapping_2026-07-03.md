# БАГ-009: DOM-debug `admin` офферов показал живые сбои `Воксис`, `ВкусВилл`, `Самокат`

## Симптом

У `admin` нужно проверять не только логи полного цикла, а реальный DOM-путь заполнения офферов через browser-runner.

На live 2026-07-03 owner-scoped DOM-прогон по `_readback_offer_mapping('admin')` через реальный `vbiv.form_proxy_url` дал:

- `Дикси` — форма отправляется;
- `X5` — форма отправляется;
- `Онекта` — форма отправляется;
- `Onecta #2` — форма отправляется;
- `Я еда` — форма отправляется;
- `Ozon` — форма отправляется;
- `Воксис` — `Page.goto: net::ERR_TIMED_OUT` на самом `pxl.leads.su/click/...`;
- `ВкусВилл` — лендинг открывается, но pre-submit state остаётся пустым по `NAME/PHONE`;
- `Самокат` — уходит на `http://work.jobs-samokat.ru/disabled.html`.

## Зона системы

- `/root/TrafficHub/modules/platforms/lovko.py`
- `/root/TrafficHub/modules/platforms/leadsu.py`
- `/root/TrafficHub/modules/vbiv_bot.py`
- `/root/TrafficHub/api/routers/offers.py`
- owner config `admin -> offer_mapping`
- owner config `admin -> vbiv.form_proxy_url`

## Гипотеза

1. `Воксис` сейчас ломается не на заполнении формы, а раньше: click-url `pxl.leads.su` не отдаёт рабочий redirect из live browser-path.
2. `Самокат` не сломан в раннере: партнёрская ссылка переводит на `disabled.html`.
3. `ВкусВилл` остаётся живым продуктовым багом формы: после промежуточных шагов page state теряет или не фиксирует `input[name="NAME"]` и `input[name="PHONE"]` до submit.

## Проверка

- На live внутри `traffichub_app` запущен Chromium через production form-proxy:
  - proxy IP подтверждён как `217.29.62.68`
  - geo-check: `RU / Moscow`
- Прогон сделан по всем 9 офферам `admin`, включая `enabled` и `disabled`.
- На каждый оффер сохранён DOM result:
  - `final_url`
  - `title`
  - `body` fragment
  - screenshot
- Артефакты прогона:
  - `/app/data/dom-offer-debug-admin/01_Дикси.png`
  - `/app/data/dom-offer-debug-admin/02_X5.png`
  - `/app/data/dom-offer-debug-admin/03_Воксис.png`
  - `/app/data/dom-offer-debug-admin/04_Онекта.png`
  - `/app/data/dom-offer-debug-admin/05_ВкусВилл.png`
  - `/app/data/dom-offer-debug-admin/06_Onecta__2.png`
  - `/app/data/dom-offer-debug-admin/07_Я_еда.png`
  - `/app/data/dom-offer-debug-admin/08_Ozon.png`
  - `/app/data/dom-offer-debug-admin/09_Самокат.png`
- Для `ВкусВилл` отдельно подтверждено:
  - `input[name="BORN"]` остаётся заполненным;
  - `input[name="NAME"]` и `input[name="PHONE"]` к моменту pre-submit проверки пустые;
  - ручной ввод в эти поля на уже открытой форме после возврата из `platform.fill()` сохраняется, значит дефект сидит в последовательности шагов внутри `_fill_vkusvill()`, а не в недоступности самих инпутов.

## Наблюдение

- DOM-debug обязателен для Autofill offer bugs: requests-only smoke не даёт достаточной картины.
- `Самокат` не надо выключать из конфигурации, но текущий live landing у партнёра терминально disabled.
- `Воксис` сейчас выглядит как внешний сетевой/redirect дефект конкретной ссылки, а не как regression в локаторе формы.
- `ВкусВилл` — единственный подтверждённый внутренний баг заполнения формы из этого прогона.

## Вывод

На 2026-07-03 реальный статус офферов `admin` по DOM-пути такой:

- 6 офферов реально отправляются;
- `Самокат` заблокирован партнёрской landing page;
- `Воксис` зависает на click-url до открытия landing;
- `ВкусВилл` требует отдельного исправления в `_fill_vkusvill()` по порядку действий перед submit.

## Следующий шаг

1. Разобрать `_fill_vkusvill()` пошагово от выбора города/склада до submit и найти точный шаг, который обнуляет `NAME/PHONE`.
2. Для `Воксис` проверить redirect chain отдельно от Playwright и подтвердить, отдаёт ли `pxl.leads.su` рабочий landing вообще.
3. Для `Самокат` зафиксировать в wiki, что текущий live symptom — partner disabled landing, а не локальный баг раннера.
