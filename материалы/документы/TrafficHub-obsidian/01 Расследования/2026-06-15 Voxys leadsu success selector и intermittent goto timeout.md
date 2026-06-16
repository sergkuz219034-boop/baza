# 2026-06-15 Voxys leadsu success selector и intermittent goto timeout

## Симптом

- `Воксис` у owner-профилей периодически падал в двух режимах:
  - `Страница оффера не открылась: Page.goto: net::ERR_TIMED_OUT ...`
  - `leadsu: форма не подтверждена после отправки`
- Исторически в логах также встречалось `leadsu: кнопка submit не найдена`, но на свежем live HTML кнопка была.

## Зона системы

- `modules/vbiv_bot.py`
- `modules/platforms/base.py`
- `modules/platforms/leadsu.py`
- runtime debug artifacts `data/debug/debug_Воксис_*.html`
- worker container `traffichub_worker`

## Гипотеза

1. Для `leadsu` оффера через proxy не хватало retry/timeout на landing redirect `pxl.leads.su -> voxys-rabota.ru`.
2. Success detector в `BasePlatform._wait_success()` был слишком узким:
   - проверял только `loc.first.is_visible()` у комбинированного `success_selector`;
   - если первый match оставался hidden, а видимым становился другой match (`.fancybox-content`, `.pu_container`), статус `ok` не фиксировался.

## Проверка

1. Live config снимался внутри `traffichub_worker`, а не на хосте:
   - подтверждено, что `admin` имеет 3 оффера: `Онекта`, `Ozon`, `Воксис`.
   - `debug-worker-a` был сужен до одного оффера `Воксис`.
2. По `debug_Воксис_20260615_181533.html` подтверждено:
   - есть `form#vacancy_form`;
   - есть `button#send_form`;
   - успех уходит в hidden popup `#hidden-content` и `fancybox`.
3. Инструментальный Playwright прогон показал:
   - до submit `#send_form` видим и стабильно находится;
   - прямой `platform.fill()` до фикса доходил до `leadsu: форма не подтверждена после отправки`;
   - отдельные запуски действительно ловили `Page.goto: net::ERR_TIMED_OUT`.
4. В live source внесены минимальные правки:
   - `modules/platforms/base.py`: success selector теперь проверяет любой видимый match, а не только `first`;
   - `modules/vbiv_bot.py`: для `platform == leadsu` и `pxl.leads.su` увеличены `max_nav_attempts` и `nav_timeout_ms`.
5. Патч синхронизирован в `traffichub_worker` и `autolead_server_bot` через `docker cp`.
6. После патча выполнены 3 подряд owner-scoped debug send запуска на `debug-worker-a`:
   - все 3 завершились `[OK] Оффер Воксис успешно заполнен! (11-12с)`.
7. Дополнительная live-проверка `2026-06-15` по `admin` показала новый cross-offer дефект:
   - при одном последовательном `send` на кандидате с тремя офферами `Онекта + Ozon + Воксис`
   - `Ozon` мог проходить,
   - `Воксис` мог уходить в `дубль`,
   - а `Онекта` периодически падала на `Page.goto: net::ERR_TIMED_OUT at https://pxl.leads.su/...`.
8. Отдельный сетевой smoke внутри `autolead_server_bot` подтвердил:
   - `requests.get()` к `pxl.leads.su` работает и без proxy, и через proxy;
   - `Playwright page.goto()` к тому же `pxl.leads.su` без proxy открывает финальный лендинг `rabotadoma.site`;
   - `Playwright page.goto()` к тому же URL через proxy стабильно даёт `net::ERR_TIMED_OUT`.
9. После этого в live source внесены ещё две правки в `modules/vbiv_bot.py`:
   - каждая анкета теперь запускается в отдельном Chromium browser instance, а не только в новом context;
   - proxy больше не глобальный для всех офферов, а включается выборочно только для тех маршрутов, которым он реально нужен (`lovko/Ozon` path).
10. После rebuild `autolead_bot` выполнен реальный `admin` smoke на одном pending-кандидате `Эльвира Джафарова`:
    - `Онекта` -> `[OK]` после повторного submit-path `tilda`;
    - `Ozon` -> `[OK]`;
    - `Воксис` -> `[~] дубль`;
    - итог `ошибок=0`.
11. На `2026-06-16` это повторно подтверждено прямым server-read:
    - в `modules/vbiv_bot.py` есть helper `_launch_browser(use_proxy=...)`;
    - внутри offer-loop браузер создаётся строкой `browser = _launch_browser(use_proxy=use_form_proxy)`;
    - в `finally` каждого оффера есть `browser.close()`.

## Наблюдение

- Источник истины по конфигам находится в container runtime, а не в хостовом `load_user_config()`.
- Ошибка `submit not found` на свежем DOM не воспроизвелась; фактический живой дефект был в success detection и flaky landing.
- `Воксис` стал стабильным на изолированном debug-профиле после двух точечных правок без перестройки общей логики sender.
- Следующий подтверждённый слой проблемы был уже не в DOM `Воксис`, а в общей browser/proxy стратегии sender:
  - reuse браузера между офферами загрязнял partner-click session;
  - глобальный proxy для всех форм ломал `pxl.leads.su` / `Онекта`, хотя был полезен для `Ozon`.

## Вывод

- Для `leadsu/Воксис` было две независимые runtime-проблемы:
  - intermittent proxy/redirect timeout на landing;
  - false negative в определении успешной отправки.
- Минимальный рабочий фикс:
  - расширенный nav retry/timeout в `modules/vbiv_bot.py`;
  - проверка любого видимого `success_selector` в `modules/platforms/base.py`.
- Для стабильного multi-offer send этого было недостаточно.
- Подтверждённый live fix на `2026-06-15`:
  - `one-offer = one-browser`;
  - form proxy не должен применяться ко всем анкетам глобально;
  - `lovko/Ozon` остаются на proxy-path, а `pxl.leads.su` / `Онекта` должны открываться без него.
- Это правило теперь считать runtime-инвариантом sender, а не временным hotfix.

## Следующий шаг

1. Проверить тот же runtime-contract через UI-кнопки `Рассылка` и `Полный цикл`, а не только через container smoke.
2. Если в live снова появится `Page.goto timeout` для `Воксис` или `Онекта`, сначала смотреть:
   - container runtime version файлов;
   - не включился ли proxy для `pxl.leads.su` маршрута повторно;
   - свежий `debug_Воксис_*.html`.
3. Отдельно разобрать stuck owner `artem` в Redis `status=stopping`, потому что это уже другая зона проблемы.
