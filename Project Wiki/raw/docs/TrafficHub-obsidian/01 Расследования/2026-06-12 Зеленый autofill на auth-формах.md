# 2026-06-12 Зеленый autofill на auth-формах

## Симптом

- браузер подставлял логин и пароль на auth-формах жёлтым фоном;
- пользователь попросил заменить жёлтый фон строк ввода на зелёный.

## Зона системы

- `dashboard/style.css`
- `api/server.py`
- browser autofill (`-webkit-autofill`) на login/register формах

## Гипотеза

- жёлтый цвет задавался не приложением, а встроенным autofill-стилем Chromium;
- обычный `background` у `input` не перекрывал autofill-state, поэтому нужно отдельное CSS-правило для `:-webkit-autofill`.

## Проверка

- на сервере подтверждено, что в `dashboard/style.css` не было override для `:-webkit-autofill`;
- в shared register style (`_REGISTER_SHARED_STYLE` внутри `api/server.py`) такого override тоже не было;
- добавлены правила:
  - `input:-webkit-autofill`
  - `input:-webkit-autofill:hover`
  - `input:-webkit-autofill:focus`
  - `input:-webkit-autofill:active`
  - для register дополнительно `textarea:-webkit-autofill*`
- стиль autofill переведён на зелёную заливку через inset box-shadow:
  - `rgba(51, 156, 13, 0.22)`
  - border `rgba(94, 179, 61, 0.65)`
- первая версия override без `!important` оказалась недостаточно жёсткой: Chromium продолжал местами показывать жёлтую заливку;
- runtime-правка усилена:
  - `-webkit-text-fill-color: ... !important`
  - `background-color: transparent !important`
  - `box-shadow` / `-webkit-box-shadow` с `!important`
  - очень длинный `transition: background-color ... !important`
- пересобран и перезапущен `autolead_server_bot`;
- runtime-status после правки: `healthy`.

## Наблюдение

- проблема была не в login-template и не в форме как таковой;
- это браузерный системный стиль, поэтому без явного `-webkit-autofill` override жёлтый фон будет возвращаться;
- для Chromium в этом кейсе обычного override без `!important` оказалось недостаточно;
- правка применена и к login, и к register, чтобы auth-flow не расходился визуально.

## Вывод

- жёлтый фон был следствием Chromium autofill, а не server-side темы;
- корректная точка фикса — CSS-override на auth-формах;
- теперь autofill-поля на auth-экранах должны выглядеть зелёными, а не жёлтыми.

## Следующий шаг

- если позже понадобится единый auth-style source, autofill overrides стоит вынести в общий shared auth CSS вместо дублирования между `dashboard/style.css` и `_REGISTER_SHARED_STYLE`.
