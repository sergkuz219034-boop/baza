# БАГ-032: Ozon на `lovko` периодически падал на `Page.goto: net::ERR_TIMED_OUT`

## Симптом

В `autolead.log` полный цикл доходил до send-фазы и в целом продолжал работу, но по `Ozon` регулярно появлялись ошибки вида:

- `Ошибка Ozon [...]: Страница оффера не открылась: Page.goto: net::ERR_TIMED_OUT at https://tracking.lovko.pro/click?...offer_id=22`

При этом соседние попытки по тому же офферу часто завершались успешно.

## Зона системы

- `/root/TrafficHub/modules/vbiv_bot.py`
- `lovko` offer navigation contour
- `tracking.lovko.pro/click?...offer_id=22`

## Гипотеза

`Ozon` попадал в общий `lovko` navigation-profile, хотя по runtime-поведению это медленный маршрут, ближе к уже выделенным slow-route кейсам (`Samokat`, `logystpartner`).

Из-за этого:

- число попыток открытия было слишком маленьким;
- timeout открытия был слишком коротким для части запросов;
- случайные сетевые задержки превращались в user-visible error, хотя следующий запуск часто проходил успешно.

## Проверка

- Локальный лог `autolead.log` подтвердил повторяющийся паттерн:
  - несколько `ERR_TIMED_OUT` на `offer_id=22`;
  - между ними множество успешных `Оффер Ozon успешно заполнен!`.
- В `modules/vbiv_bot.py` подтверждено, что slow-route профиль раньше применялся только к:
  - `Samokat`;
  - `jobs-samokat.ru`;
  - `logystpartner.ru`;
  - `leadsu`.
- Для `Ozon/lovko` был добавлен отдельный helper `_is_slow_lovko_route(offer_name, current_url)`, который теперь считает slow-route также:
  - `offer_name` содержит `ozon`;
  - `current_url` содержит `offer_id=22`.
- Добавлен regression test:
  - `tests/test_vbiv_bot_navigation.py`
- Targeted verification в live-контуре:
  - `docker exec autolead_server_bot pytest -q tests/test_vbiv_bot_navigation.py tests/test_platform_routing.py tests/test_leadsu_blank_recovery.py`
  - результат: `19 passed`

## Наблюдение

Проблема была не в полном падении платформы `lovko` и не в permanently broken offer.

Confirmed fact:

- `Ozon` был пограничным медленным маршрутом;
- общий `lovko` timeout-profile был для него слишком агрессивным;
- runtime уже умел лечить похожие slow-route кейсы, но `offer_id=22` не был включён в этот контур.

## Вывод

`Ozon` стабилизирован через расширение slow-route логики в `vbiv_bot`.

Теперь для `Ozon/lovko` применяются усиленные navigation retries и timeout'ы до входа в platform fill path.

Это снижает количество ложных `Page.goto timeout` ошибок без изменения логики заполнения формы.

## Следующий шаг

1. При следующих жалобах на `lovko`-timeouts сначала проверять, не относится ли новый оффер к slow-route классу.
2. Если в логах появится другой систематически медленный `lovko` URL, расширять `_is_slow_lovko_route()` через code+test, а не через разовые hotfix.
3. Держать канон проверки: лог -> code path -> targeted pytest -> live rebuild.
