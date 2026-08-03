# Playwright TargetClosedError после заполнения анкеты

## Симптом

В логе рассылки после успешного заполнения анкеты появлялись сообщения `Task was destroyed but it is pending` и `TargetClosedError: Target page, context or browser has been closed`.

## Зона системы

`modules/vbiv_bot.py`, функция `run_campaign`, жизненный цикл Playwright browser/context.

## Гипотеза

Один экземпляр браузера закрывался дважды: в `finally` конкретного оффера и затем во внешнем `finally` кампании.

## Проверка

Проверен код на production (`/root/TrafficHub/modules/vbiv_bot.py`) и внутри обоих рабочих контейнеров.

## Наблюдение

После `browser.close()` ссылка `browser` сохранялась. Внешний cleanup видел ту же ссылку и вызывал повторный `close()`, из-за чего Playwright оставлял отменяемую async-задачу и печатал предупреждение.

## Вывод

Это ошибка cleanup, а не неуспех отправки: в тех же запусках оффер был заполнен успешно. Повторное закрытие устранено коммитом production `334542fca` (`fix: close Playwright browser once`): после закрытия `context` и `browser` ссылки обнуляются; восстановление после ошибки создания контекста также обнуляет старый browser.

## Следующий шаг

Наблюдать ближайший полный цикл. Если предупреждение повторится, сохранить точный log timestamp и расследовать отдельный путь принудительной остановки (`/stop`).
