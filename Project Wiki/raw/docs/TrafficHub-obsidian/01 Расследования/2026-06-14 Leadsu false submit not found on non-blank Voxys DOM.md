# 2026-06-14 Leadsu false submit not found on non-blank Voxys DOM

## Симптом

- В live `traffichub_worker` для `artem/run` были подтверждены ошибки:
  - `Ошибка Воксис [1]: leadsu: форма не подтверждена после отправки`
  - `Ошибка Воксис [1]: leadsu: кнопка submit не найдена`
- При этом debug-артефакт для `debug_Воксис_20260614_173030.html` уже содержал нормальную HTML-форму `VOXYS`, а не blank DOM.

## Зона системы

- Live code:
  - `/root/TrafficHub/modules/platforms/leadsu.py`
  - `/root/TrafficHub/modules/platforms/base.py`
  - `/root/TrafficHub/modules/vbiv_bot.py`
- Debug artifacts:
  - `/root/TrafficHub/data/debug/debug_Воксис_20260614_173030.html`
  - `/root/TrafficHub/data/debug/debug_Воксис_20260614_173030.png`

## Гипотеза

- Это уже не тот же класс дефекта, что в [[2026-06-14 Leadsu blank DOM before submit on Voxys]].
- На непустой странице детектор submit-кнопки был слишком жёстким:
  - искал `#send_form` только если `is_visible() == true`;
  - fallback по role/text тоже отдавал только visible-кнопки.
- При proxy/slow rendering кнопка могла существовать в DOM, но временно не проходить `is_visible()`, из-за чего runtime возвращал ложный `submit not found`.
- Для медленного AJAX submit `timeout=30` в `_wait_success()` был слишком коротким.

## Проверка

- Из live логов `traffichub_worker` на `2026-06-14 17:28-17:30 UTC` подтверждено:
  - часть `Воксис` шла как `[OK]` и `[~]`;
  - часть падала на `submit not found` и `форма не подтверждена после отправки`.
- Из debug HTML подтверждено:
  - страница содержит:
    - `<form id="vacancy_form">`
    - `<button id="send_form"> Отправить анкету </button>`
    - success-блок `#hidden-content`
  - значит ошибка `submit not found` была ложным negative детектора, а не отсутствием кнопки в DOM.
- После hotfix в live source `/root/TrafficHub/modules/platforms/leadsu.py` подтверждено:
  - `_find_submit_button()` теперь возвращает кнопку и если она есть в DOM, даже если `is_visible()` transient false;
  - добавлен `_click_submit_button()` с fallback:
    - обычный `click(force=True)`
    - `el.click()` через JS
    - JS-поиск submit по DOM-селекторам
  - `timeout` ожидания подтверждения поднят с `30` до `45` секунд.
- Узкий test contour:
  - `pytest -q tests/test_leadsu_blank_recovery.py`
  - результат: `2 passed`
- Safe replay на реальном failing DOM внутри контейнера, без внешней сети:
  - открыт `file:///app/data/debug/debug_Воксис_20260614_173030.html`
  - подтверждено:
    - `BUTTON_FOUND True`
    - `BUTTON_TEXT Отправить анкету`
    - `CLICK_FALLBACK_OK True`

## Наблюдение

- Blank DOM и false submit detection — это два разных runtime-класса дефектов.
- Первый лечится reload/recovery до submit.
- Второй лечится более мягким детектором DOM-кнопки и fallback-кликом.
- Hotfix был залит не только в source tree `/root/TrafficHub`, но и прямо в файловую систему контейнеров:
  - `traffichub_worker:/app/modules/platforms/leadsu.py`
  - `autolead_server_bot:/app/modules/platforms/leadsu.py`
- Причина: compose использует `build: .`, а не bind mount исходников; hotfix нужен был без остановки активных owner-run.

## Вывод

- На `2026-06-14` подтвержден отдельный live-баг:
  - `LeadsuPlatform` могла ошибочно заявлять `кнопка submit не найдена`, хотя кнопка физически была в DOM `Воксис`.
- Подтверждённый safe fix:
  - ослабить критерий поиска submit до `кнопка есть в DOM`;
  - добавить JS fallback click;
  - дать больше времени на post-submit confirmation при медленном proxy/AJAX.

## Следующий шаг

- После завершения активных owner-run выполнить нормальную пересборку и перезапуск:
  - `docker compose build autolead_bot worker`
  - `docker compose up -d autolead_bot worker`
- При следующем live инциденте сравнить:
  - остались ли `leadsu: кнопка submit не найдена`
  - сократилось ли число `leadsu: форма не подтверждена после отправки`
  - не появился ли regression на дублях `Воксис`.
