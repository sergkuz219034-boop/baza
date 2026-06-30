---
title: 2026-06-30 AccountManager hidden dialog drawer blocks header buttons
---

# 2026-06-30 AccountManager hidden dialog drawer blocks header buttons

## Симптом

- В live `AccountManager` пользователь видел, что часть кнопок в header "не нажимается", в первую очередь `Проверить всё` и `+ Добавить аккаунт`.

## Зона системы

- `AccountManager` frontend.
- Файлы:
  - `AccountManager/dashboard/index.html`
  - `AccountManager/dashboard/style.css`
  - `AccountManager/dashboard/app.js`

## Гипотеза

- Не backend-ошибка, а фронтовый слой поверх header перехватывает pointer events.

## Проверка

- Подтверждён healthy контейнер `traffichub_account_manager`.
- `https://am.traffic-hub.pro/api/health` вернул `{"status":"ok"}`.
- Headless browser-probe внутри контейнера с admin JWT открыл `http://127.0.0.1:8000/?token=...` и попытался кликнуть `#btn-health` и `#btn-open-account`.
- До фикса Playwright возвращал ошибку вида: hidden `dialog-drawer` subtree intercepts pointer events.
- Код `AccountManager/dashboard/app.js` показал, что drawer закрывается через снятие класса `.open` и установку HTML-атрибута `hidden`.
- Код `AccountManager/dashboard/style.css` показал, что `.dialog-drawer` имеет `display: grid`, а явного правила для `.dialog-drawer[hidden]` не было.

## Наблюдение

- CSS-класс `.dialog-drawer` переопределял browser default для атрибута `hidden`.
- В результате закрытый drawer оставался `position: fixed` поверх интерфейса с `opacity: 0`, но продолжал ловить клики.
- Это объясняет "ломаются разные кнопки" без JS-ошибок и без failed network requests.

## Вывод

- Root cause: скрытый `dialog-drawer` Telegram-переписок перекрывал header.
- Фикс в live/product repo:
  - для `.dialog-drawer` и `.dialog-drawer-overlay` добавлены `pointer-events: none` по умолчанию;
  - для `[hidden]` добавлены `display: none !important`;
  - для `.open` возвращаются `pointer-events: auto`.
- После hotfix и restart контейнера browser-probe повторно подтвердил успешные клики по `#btn-health` и `#btn-open-account`, без JS/network ошибок.

## Следующий шаг

- Если пользователь сообщает о других "мертвых" кнопках, проверять их уже точечно через browser-probe по конкретным selectors, а не считать общим сбоем backend.
