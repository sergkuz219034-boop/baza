# БАГ-007: admin не заполнял Lovko/VkusVill офферы без form-proxy и ломался на Onecta #2

## Симптом

У `admin` полный цикл доходил до send-фазы, но офферы `Дикси`, `X5`, `ВкусВилл`, `Onecta #2` не отправлялись.

- `Дикси`, `X5`, `Onecta #2` падали на `Page.goto: net::ERR_TIMED_OUT`.
- `ВкусВилл` падал на `vpn detected`.
- После включения рабочего proxy `Onecta #2` начал открываться, но форма падала на `lovko: форма не подтверждена после отправки`.

## Зона системы

- `/app/modules/vbiv_bot.py`
- `/app/modules/platforms/lovko.py`
- `control_user_app_configs.login='admin'`
- live proxy `http://uE0D08:LZCcvM@217.29.62.68:8000`

## Гипотеза

1. Проблема Lovko-офферов была не в самих ссылках, а в том, что production-сервер открывал их без browser form-proxy.
2. После починки сетевого доступа `Onecta #2` падал уже на frontend-валидации формы BetaOnline: часть обязательных полей не закреплялась в DOM перед submit.

## Проверка

- Прямой `requests.get()` с сервера:
  - без proxy `Дикси`, `X5`, `Onecta #2` таймаутились;
  - без proxy `ВкусВилл` открывал `vpn-detected`;
  - с proxy все 4 URL открывались с `200`.
- В `admin` config включён только browser-fill proxy:
  - `vbiv.form_proxy_enabled = true`
  - `vbiv.form_proxy_url = http://uE0D08:LZCcvM@217.29.62.68:8000`
- Точечный live send на лиде `Марина Горбенко / 9045835655` подтвердил успешную отправку:
  - `Дикси`
  - `X5`
  - `ВкусВилл`
  - `Onecta #2`
- Debug artifacts `debug_Onecta__2_20260618_130119.*` показали реальную причину второго сбоя:
  - форма открывалась;
  - обязательные поля `Наличие ПК`, `Статус самозанятого`, `Ваш город` оставались невалидными после первого submit.
- В `/app/modules/platforms/lovko.py` добавлен retry-fallback:
  - если после первого submit успех не подтверждён и обязательные поля всё ещё пустые;
  - раннер дозаполняет `nalichie-pk`, `status-samozanyatogo`, `place_of_residence`;
  - затем делает повторный submit.
- После патча точечный live send на лиде `Анна Почепа Сергеевна / 9897571213` подтвердил успешный `Onecta #2`.
- В live full-cycle `admin` после включения proxy появились подтверждённые успехи:
  - `Дикси успешно заполнен`
  - `X5 успешно заполнен`
  - `ВкусВилл успешно заполнен`

## Наблюдение

- Корневой дефект был двухслойный:
  - сетевой доступ до Lovko/VkusVill с server IP;
  - нестабильная post-submit фиксация обязательных полей на BetaOnline-форме `Onecta #2`.
- `rabota_ru.proxy_enabled` для этого кейса не обязателен; достаточно browser form-proxy в `vbiv`.
- Ошибка `Onecta #2` больше не относится к категории network/proxy.

## Вывод

Проблема admin-офферов исправлена через:

1. browser form-proxy для Lovko/VkusVill;
2. дополнительный retry-fallback в `LovkoPlatform` для обязательных полей формы BetaOnline.

Подтверждённый live-результат:

- `Дикси` — отправляется;
- `X5` — отправляется;
- `ВкусВилл` — отправляется;
- `Onecta #2` — отправляется после патча `lovko.py`.

## Следующий шаг

1. Довести рабочую копию исходников до канонического репозитория, чтобы fix не жил только в runtime-контейнере.
2. Добавить regression test на betaonline-форму с обязательными полями `nalichie-pk`, `status-samozanyatogo`, `place_of_residence`.
3. Зафиксировать proxy-contract в [[02_Код/Эксплуатация/Конфигурация]] и [[02_Код/Архитектура/Интеграции]].
