# 2026-06-25 AccountManager вкладка TrafficHub внизу sidebar

## Симптом

Во `[[AccountManager]]` внешний переход `TrafficHub` стоял первым блоком sidebar и визуально опережал рабочие разделы `Операции`, `Контент`, `API Gateway`, `ИИ Агент`, `Система`.

## Зона системы

- `/root/TrafficHub/AccountManager/dashboard/index.html`
- `/root/TrafficHub/CHANGELOG.md`

## Гипотеза

Порядок sidebar задаётся статическим HTML, а не JS-сортировкой. Для переноса ссылки вниз достаточно переставить весь `sidebar-group` блока `TrafficHub` после `Система`.

## Проверка

- На live host в `/root/TrafficHub/AccountManager/dashboard/index.html` подтверждён отдельный блок:
  - `sidebar-label: TrafficHub`
  - `button.external-link` с `window.open('https://traffic-hubcrm.ru', '_blank')`
- JS в `AccountManager/dashboard/app.js` не перестраивает порядок sidebar-групп.
- После правки `git diff` показывает только перенос одного HTML-блока без изменения URL или поведения кнопки.

## Наблюдение

Это чистый layout-order fix в общем шаблоне AccountManager. Runtime-логика, auth и маршруты не затронуты.

## Вывод

Кнопку `TrafficHub` нужно держать внизу sidebar как внешний переход, чтобы она не конкурировала с основным рабочим меню AccountManager.

## Следующий шаг

- После deploy проверять визуально, что sidebar открывается в порядке:
  `Операции -> Контент -> API Gateway -> ИИ Агент -> Система -> TrafficHub`.
