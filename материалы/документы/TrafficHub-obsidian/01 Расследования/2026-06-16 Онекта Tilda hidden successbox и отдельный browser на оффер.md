# 2026-06-16 Онекта Tilda hidden successbox и отдельный browser на оффер

## Симптом

- `Онекта` в live runtime продолжала падать с `tilda: форма не подтверждена после отправки`;
- при этом ручной post-submit probe показывал, что форма визуально заполнена корректно и явных validation errors нет;
- параллельно нужно было подтвердить runtime-contract: каждая анкета должна открываться в отдельном браузере, чтобы партнёрский клик считался уникальным.

## Зона системы

- `modules/platforms/tilda.py`
- `modules/vbiv_bot.py`
- runtime container `autolead_server_bot`
- live config пользователя `admin`

## Гипотеза

1. Проблема `Онекта` находится не в заполнении полей, а в детекторе успешной отправки Tilda.
2. Tilda может успешно принять форму, но не показать success-блок как `visible`, из-за чего общий `_wait_success()` возвращает `failed`.
3. Требование “каждая анкета = новый браузер” уже могло быть выполнено кодом, но должно быть подтверждено именно по live source-of-truth.

## Проверка

1. Live probe внутри `autolead_server_bot` по `admin` + первый pending lead:
   - `offer.target_url` для `Онекта`:
     - `https://pxl.leads.su/click/fcc893f7865de8e11d851cd3c0506a93?erid=2W5zFGM1hbE`
   - форма после submit реально отправляла `POST https://forms.tildacdn.com/procces/`;
   - request body содержал:
     - `name=Вероника ШЛЯХОВСКАЯ`
     - `Phone=+79920534803`
     - `гражданство=Российская Федерация`
     - `tg_username=+79920534803`
2. DOM probe после неуспешного `platform.fill()` показал:
   - `.js-successbox.t-form__successbox` существует;
   - внутри уже есть текст:
     - `Спасибо!`
     - `Ваши данные успешно отправлены.`
     - `Свяжемся с вами в ближайшее время.`
   - но этот блок остаётся `display:none`;
   - visible input errors не обнаружены;
   - visible errorbox с текстом не обнаружен.
3. По live коду `modules/vbiv_bot.py` подтверждено:
   - внутри цикла офферов перед каждым `platform_impl.fill()` выполняется:
     - `browser = _launch_browser(use_proxy=use_form_proxy)`
     - затем `context, page = _make_context(browser, ...)`
   - в `finally` того же блока выполняется:
     - `context.close()`
     - `browser.close()`
   - это подтверждает runtime-contract:
     - один оффер / одна анкета -> отдельный Chromium browser instance;
     - browser не переиспользуется между соседними офферами.
4. В `modules/platforms/tilda.py` внесён точечный live fix:
   - добавлен helper `_has_hidden_success_state(page)`;
   - после обычного `_wait_success()` рантайм теперь дополнительно проверяет hidden successbox;
   - если success-текст уже есть и видимых error state нет, форма считается успешно отправленной.
5. После `docker compose build autolead_bot worker && docker compose up -d autolead_bot worker` выполнен live smoke:
   - `Онекта`:
     - `[OK] Оффер Онекта успешно заполнен! (34с)`
   - повторный прогон:
     - `[OK] Оффер Онекта успешно заполнен! (42с)`
6. Дополнительный минимальный Playwright smoke для `Ozon` внутри `autolead_server_bot` подтвердил:
   - direct route -> `net::ERR_TIMED_OUT`
   - proxy route -> успешный переход на `https://vakansii-ozon.ru/...`
7. Повторный `run_campaign([lead], admin_cfg)` после rebuild:
   - `Онекта` -> success
   - `Ozon` -> success
   - `Воксис` -> дубль/ошибка уже по собственному flow, а не из-за общей деградации sender runtime

## Наблюдение

- `Онекта` ломалась не из-за полей формы и не из-за partner redirect.
- Истинная причина: Tilda success-state уже присутствовал в DOM, но оставался hidden, и старый runtime принимал это за failure.
- Для `Ozon` канон на `2026-06-16` такой:
  - direct browser path нестабилен/нерабочий;
  - proxy browser path подтверждённо рабочий;
  - проверять `Ozon` без proxy smoke бессмысленно.

## Вывод

- `Онекта/Tilda` починена через runtime-aware fallback по hidden successbox.
- Требование “каждый оффер открывается в отдельном браузере” подтверждено живым кодом `modules/vbiv_bot.py`.
- После синхронизации контейнеров и фикса hidden successbox `admin`-smoke снова даёт рабочий `Онекта + Ozon` path на одном pending lead.

## Следующий шаг

1. Отдельно стабилизировать `Воксис`, если он продолжит падать на `leadsu: форма не подтверждена после отправки`.
2. Прогнать owner-scoped `send/full cycle` уже не только на single lead smoke, а на debug-профиле с живым логом.
3. Зафиксировать в wiki и коде, что `Ozon/Lovko` runtime следует считать proxy-required офферами, пока upstream не начнёт стабильно открываться напрямую.
