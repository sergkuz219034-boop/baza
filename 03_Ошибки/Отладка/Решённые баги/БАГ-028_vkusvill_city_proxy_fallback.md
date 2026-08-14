# БАГ-028: ВкусВилл не подтверждает форму после отправки

## Симптом

- В live-логах повторяется `Ошибка ВкусВилл [1]: leadsu/vkusvill: форма не подтверждена после отправки`.
- Затем запись помечается как постоянная `form-failure`, retry queue пропускается.

## Зона системы

- Autolead form-fill.
- `modules/platforms/lovko.py`, класс `VkusvillLeadsuPlatform`.
- Браузерный proxy в `modules/vbiv_bot.py`.

## Гипотеза

- Форма не подтверждается не из-за кнопки submit, а из-за валидации города трудоустройства на стороне `vkusvill.ru`.
- Для ВкусВилл нужен тот же браузерный proxy-контур, что и для Lovko/партнёрских форм.

## Проверка

- Runtime debug HTML: `/root/TrafficHub/data/debug/debug_ВкусВилл_20260621_021931.html`.
- Runtime screenshot: `/root/TrafficHub/data/debug/debug_ВкусВилл_20260621_021931.png`.
- Live repo: `/root/TrafficHub`, commit `d94e281f1`.
- Container check: `autolead_server_bot` после rebuild/recreate.

## Наблюдение

- На screenshot после submit видно красную валидацию `Укажите город трудоустройства`.
- В debug HTML `input[name="CITY"]` пустой, `.thanks-modal` отсутствует.
- Город лида `Богучар` не выбран сайтом как валидный город ВкусВилл.
- При прямом headless-доступе к `vkusvill.ru` возможен `/vpn-detected/`, поэтому ВкусВилл должен попадать в proxy-routing.

## Вывод

- Root cause: старый алгоритм считал напечатанный город достаточным, но ВкусВилл принимает только выбор из `button.js-request-city-item`, который заполняет hidden `CITY`.
- Исправление: кандидат города строится как `город оффера -> город лида -> Москва`; успех выбора города считается только после непустого hidden `CITY`.
- Исправление также расширило browser proxy routing: `vkusvill.ru`, `vkusvill`, `вкусвилл`, `вкус вилл`.
- Это общий кодовый путь, не owner-specific, поэтому фикс применяется ко всем текущим и будущим пользователям после деплоя общего контейнера.

## Следующий шаг

- Если ошибка повторится, первый check: открыть свежий `debug_ВкусВилл_*.png/html` и проверить, заполнен ли hidden `CITY`, был ли proxy включён в настройках пользователя и нет ли нового изменения DOM на стороне `vkusvill.ru`.

