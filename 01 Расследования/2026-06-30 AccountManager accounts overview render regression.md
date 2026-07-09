---
title: 2026-06-30 AccountManager accounts overview render regression
---

# 2026-06-30 AccountManager accounts overview render regression

## Симптом

- В live `AccountManager` summary показывал `5 / 6`, но overview и таблица аккаунтов были пустыми.

## Зона системы

- `AccountManager` frontend.
- Файл: `AccountManager/dashboard/app.js`

## Гипотеза

- Данные из backend приходят, но frontend падает на рендере карточек после недавних правок Telegram action buttons.

## Проверка

- `GET /api/accounts` на live вернул `6` аккаунтов.
- Headless browser probe показал:
  - `state.accounts.length = 6`
  - `account-cards.children.length = 0`
  - `accounts-table.children.length = 0`
- Принудительный вызов `renderCards()` в браузере дал `ReferenceError: Cannot access 'authButton' before initialization`.
- Осмотр `AccountManager/dashboard/app.js` подтвердил повреждённый блок `tgButtons()`: внутрь него попали лишние строки, а куски `renderProxies()` / `renderTgWsProxy()` частично слиплись с этой функцией.

## Наблюдение

- Это был не data-loss и не backend issue.
- Один сломанный helper для Telegram action buttons уронил и карточки overview, и таблицу аккаунтов.

## Вывод

- В live/product repo восстановлены:
  - `tgButtons()`
  - `renderProxies()`
  - `renderTgWsProxy()`
- После hotfix headless browser probe подтвердил:
  - `6` карточек
  - `6` строк таблицы
  - `errors = []`

## Следующий шаг

- Для любого изменения account action helpers прогонять browser-probe на `account-cards` и `accounts-table`, потому что один `ReferenceError` там скрывает все аккаунты сразу.
