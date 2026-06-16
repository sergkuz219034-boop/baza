## Симптом

> Обновление от 13.06.2026:
> вывод этой заметки частично устарел.
> На 12.06.2026 было верно, что live runtime не доходил до формы и получал `disabled.html`, но дополнительно выяснилось:
> browser-runner в тот момент ещё и неверно разбирал proxy с авторизацией.
> См. [[2026-06-13 Ozon Lovko proxy parser bug и disabled upstream]].

- Оффер `Ozon` в Autolead "не заполняется".
- В логах раньше наблюдались `Page.goto timeout`, затем при повторной live-проверке страница открывалась как `Disabled`.

## Зона системы

- `modules/vbiv_bot.py`
- `modules/platforms/lovko.py`
- внешний upstream `tracking.lovko.pro`

## Гипотеза

- Проблема не в локальных селекторах формы, а в том, что upstream больше не отдает саму анкету для Ozon.

## Проверка

- Подтвержден runtime mapping:
  - `modules/platforms/__init__.py`
    - `ozon -> LovkoPlatform`
- Проверены live URL:
  - `https://tracking.lovko.pro/click?pid=4161&offer_id=22&sub1=1`
  - `https://tracking.lovko.pro/click?pid=41266&offer_id=22`
- Проверка выполнена внутри `autolead_server_bot` через Playwright `page.goto(..., wait_until="domcontentloaded")`.
- Снят HTML финальной страницы для Ozon.

## Наблюдение

- Для обоих Ozon URL live runtime получает:
  - `RESP 200`
  - `FINAL https://tracking.lovko.pro/disabled.html`
  - `TITLE Disabled`
- HTML страницы:

```html
<!DOCTYPE html><html><head>
    <title>Disabled</title>
</head>
<body>
    <h1>Disabled</h1>
</body></html>
```

- В DOM нет:
  - `input[name='lastname']`
  - `input[name='firstname']`
  - `input[name='mobile_phone']`
  - `select[name='city']`
- Для сравнения проверены соседние Lovko-офферы:
  - `Я.Еда` -> `disabled.html`
  - `Четыре лапы` -> `disabled.html`
  - `Дикси` -> timeout
  - `X5` -> timeout

## Вывод

- Ozon не заполняется не из-за ошибки формы в `LovkoPlatform`.
- Причина раньше пайплайна заполнения:
  - upstream не отдает анкету;
  - вместо формы возвращается `disabled.html`.
- Следствие:
  - текущие селекторы `lovko.py` для Ozon сейчас нерелевантны, потому что до формы выполнение вообще не доходит.

## Следующий шаг

- Не лечить это правкой полей анкеты.
- Нужно либо:
  - получить новый рабочий Ozon URL у партнёрки,
  - либо заменить/отключить этот оффер,
  - либо добавить в рантайм явную диагностику `disabled.html` с понятным логом:
    - `Оффер Ozon отключен на стороне партнёрки (Lovko disabled.html)`.
