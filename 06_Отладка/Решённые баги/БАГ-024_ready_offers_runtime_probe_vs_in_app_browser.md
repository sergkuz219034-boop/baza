# БАГ-024: ready-офферы нужно проверять боевым runtime, а не только in-app browser

## Симптом

При ручной проверке ready-офферов через in-app browser казалось, что часть анкет сломана:

- `tracking.lovko.pro/*` открывался с `net::ERR_BLOCKED_BY_CLIENT`;
- `ВкусВилл` показывал `vpn-detected`;
- `Воксис` доходил до JS alert, но текст ответа browser-surface не раскрывал.

Из этого можно было ошибочно сделать вывод, что ready-офферы у пользователей сломаны.

## Зона системы

- browser debug contour в Codex
- live runtime `autolead_server_bot`
- офферы `lovko` / `leadsu`

## Гипотеза

Проблема не в самих ready-офферах, а в различии двух контуров:

- in-app browser имеет свой browser policy и может блокировать трекинговые домены;
- боевой Playwright-контур `TrafficHub` использует другой runtime, другой proxy policy и другой результат навигации.

## Проверка

Ручная browser-проверка:

- `Дикси`, `X5`, `Onecta #2`:
  - `tracking.lovko.pro` -> `net::ERR_BLOCKED_BY_CLIENT`
- `Онекта`:
  - форма реально открылась и вручную отправилась с сообщением `Спасибо! Ваши данные успешно отправлены.`
- `ВкусВилл`:
  - browser-сurface открывал `vpn-detected`

После этого выполнен runtime-probe в `autolead_server_bot` на одном реальном lead `admin` без записи истории, но через тот же Playwright/platform contour, который использует продукт.

Результат probe:

- `Дикси` -> `success=True`
- `X5` -> `success=True`
- `Воксис` -> `success=True`, `duplicate=True`
- `Онекта` -> `success=True`
- `ВкусВилл` -> `success=True`
- `Onecta #2` -> `success=True`

## Наблюдение

Confirmed fact:

- in-app browser не является каноническим доказательством работоспособности ready-оффера;
- для `lovko` он может давать ложный negative из-за browser-side blocking;
- каноническая проверка должна идти через тот же runtime contour, что и продуктовый `run_campaign()`.

Отдельный confirmed fact:

- `Воксис` на проверочном lead отработал как `duplicate`, то есть submit-path живой и ответ оффера корректно распознан.

## Вывод

Если задача звучит как “проверь ready-офферы у пользователей”, нужно различать:

- browser-surface visibility/debug;
- реальную продуктовую исполнимость через live Playwright runtime.

Для финального вердикта по ready-офферам канон — боевой runtime probe, а не только ручное открытие ссылки в in-app browser.

## Следующий шаг

- при следующих жалобах на “готовый оффер не работает” сначала проверять:
  - открывается ли целевой landing в live runtime;
  - какой `platform_key` определился;
  - нужен ли proxy для этого contour;
  - какой `FillResult` возвращает platform implementation;
- browser debug использовать как вспомогательный слой, но не как единственный источник истины.
