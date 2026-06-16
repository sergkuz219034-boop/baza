# 2026-06-15 Platform fallback, disabled offer status и live debug прогон офферов

## Симптом

- Часть офферов из `offer_mapping` запускалась через `GeneralPlatform`, хотя под них уже есть специализированные движки.
- При `disabled.html` рантайм видел только ошибку текущего запуска, но не переводил оффер в постоянный статус `Оффер отключен`.
- Лента логов дёргала скролл даже без новой строки.

## Зона системы

- `modules/vbiv_bot.py`
- `modules/sheets_sync.py`
- `dashboard/app.js`
- live runtime: `data/runtime/control.db`, `autolead_server_bot`, `traffichub_worker`

## Гипотеза

1. В live-config есть офферы с пустым `partner/platform`, поэтому `run_campaign()` деградирует до `general`.
2. `lovko.py` уже умеет определить `disabled.html`, но это не сохраняется обратно в user config.
3. Скролл дёргается из-за фронтового каскада `requestAnimationFrame + setTimeout` и из-за автоскролла на spinner update.

## Проверка

- Live `modules/vbiv_bot.py` до фикса брал движок так:
  - `offer.get("partner") or offer.get("platform", "general")`
- Safe-read из `data/runtime/control.db` подтвердил:
  - у части пользователей есть офферы;
  - часть metadata по platform неполная;
  - `proxy_url` в runtime user-config хранится в битом виде и без явной подмены не годится для browser-run.
- Выполнены live debug-прогоны через Playwright с явным proxy `217.29.62.68:8000:uE0D08:LZCcvM`.

## Наблюдение

- Подтверждено реальным прогоном:
  - `Дикси` -> success
  - `ВкусВилл` -> success
  - `Воксис` -> success
  - `Самокат` -> success
  - `Четыре лапы` -> redirect на `disabled.html`
  - `Онекта` -> лендинг открывается, используется `TildaPlatform`, но `fill()` возвращает `tilda: форма не подтверждена после отправки`
- Для `Онекта` сохранён trace:
  - `trace_pre_Онекта_20260615_011011.html`
  - `trace_post_Онекта_20260615_011011.html`
- Для `Онекта` уже подтверждено:
  - проблема не в открытии страницы;
  - проблема не в отсутствии формы;
  - проблема остаётся в post-submit path.
- Для логов подтверждено:
  - автоскролл должен срабатывать только на добавление новой строки;
  - обновление transient spinner не должно двигать scroll position.

## Вывод

- В live-runtime внесены изменения:
  - `modules/vbiv_bot.py`
    - добавлен fallback `_resolve_platform_key(offer)` по `name + target_url`;
    - user-facing лог `-> Заполняем:` больше не должен показывать внутренний `platform`;
    - disabled-offer получает persisted status `disabled` и исключается из следующих запусков;
  - `modules/sheets_sync.py`
    - добавлен terminal status `offer_disabled`;
    - label: `Оффер отключен`;
  - `dashboard/app.js`
    - скролл переведён на один `requestAnimationFrame`;
    - spinner update не должен сам вызывать автоскролл.

## Следующий шаг

1. Дочитать `trace_post_Онекта_20260615_011011.html` и сравнить с `trace_pre_*`.
2. Отдельно прогнать `Я еда` тем же trace-подходом.
3. Проверить UI-отображение persisted status `Оффер отключен`.
