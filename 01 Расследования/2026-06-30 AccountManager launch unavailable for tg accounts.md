---
title: 2026-06-30 AccountManager launch unavailable for tg accounts
---

# 2026-06-30 AccountManager launch unavailable for tg accounts

## Симптом

- В `AccountManager` у текущих Telegram-аккаунтов в overview и таблице показывалась кнопка `Запуск недоступен`.

## Зона системы

- `AccountManager` frontend и Telegram profile launch UX.
- Файлы:
  - `AccountManager/dashboard/app.js`
  - `AccountManager/utils/tg_profiles.py`

## Гипотеза

- Текущие аккаунты не сломаны; интерфейс ошибочно трактует Linux runtime-ограничение как поломку самих Telegram-профилей.

## Проверка

- Для live TG-аккаунтов `1, 3, 4, 5, 6, 7` `tg_profile_status()` вернул `active` и сообщение уровня `Профиль AyuGram найден, tdata выглядит рабочей`.
- У большинства аккаунтов `executable_path = null`, у `Виктория` указан Windows-путь `Telegram.exe`.
- Прямой вызов `launch_tg_profile()` подтвердил:
  - для `Telegram.exe` в Linux container возвращается ожидаемое runtime-ограничение;
  - для аккаунтов без binary возвращается `Не указан существующий Telegram.exe/AyuGram.exe`.
- `AccountManager/dashboard/app.js` показывал `Запуск недоступен`, если:
  - `executable_path` пустой; или
  - binary заканчивается на `.exe`.

## Наблюдение

- UI смешивал две разные ситуации:
  - `tdata` аккаунта валиден и доступен для Telethon;
  - server-side запуск GUI Telegram Desktop из Linux container невозможен.
- Из-за этого пользователь видел мёртвую кнопку как будто аккаунт сломан, хотя переписки и авторизация через Telethon были рабочими.

## Вывод

- Root cause: неверный UX-предикат в `tgButtons()`, а не дефект текущих Telegram-аккаунтов.
- В live/product repo вместо `Запуск недоступен` для таких аккаунтов теперь показываются:
  - `Переписки`
  - `Почему нет запуска`
  - `Авторизация`
- Если когда-либо появится Linux-совместимый Telegram binary и live `process_id`/launch workflow, обычная кнопка `Запуск` остаётся доступной.

## Следующий шаг

- Если понадобится настоящий server-side launch, это уже отдельная задача по runtime-архитектуре: либо Windows host/agent, либо Linux-native Telegram runtime. Для текущего live contour source of truth для TG-аккаунтов — `tdata + Telethon`, а не запуск `.exe`.
