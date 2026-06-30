---
title: 2026-06-30 AccountManager content bot toggle polish
---

# 2026-06-30 AccountManager content bot toggle polish

## Симптом

- Во вкладке `Content Bot` переключатель выглядел как маленькая квадратная кнопка `ВКЛ/ВЫКЛ` и визуально не соответствовал остальному `AccountManager`.

## Зона системы

- `AccountManager` frontend.
- Файлы:
  - `AccountManager/dashboard/index.html`
  - `AccountManager/dashboard/app.js`
  - `AccountManager/dashboard/style.css`

## Гипотеза

- Проблема не в логике `bot_enabled`, а в слабой visual hierarchy и отсутствии нормальной switch-surface вокруг live control.

## Проверка

- `renderContentBotControl()` подтверждённо использует `state.contentSettings.bot_enabled`.
- До фикса UI ограничивался одной кнопкой `toggle-pill` с текстом `ВКЛ/ВЫКЛ`.
- После правки live browser probe подтвердил:
  - `ariaPressed = "false"`
  - `toggleHeight = 76`
  - `toggleWidth = 328`
  - состояние, hint и description синхронизированы с `bot_enabled`.

## Наблюдение

- Старый control выглядел как placeholder, а не как отдельный операционный switch.
- Основной выигрыш дал не только новый toggle-track, но и разделение блока на:
  - status copy
  - state pill
  - switch card

## Вывод

- В `Content Bot` применён frontend polish:
  - нормальный переключатель с track/knob;
  - отдельный статус `Бот активен/выключен`;
  - живая подсказка состояния;
  - card-surface с согласованными радиусами, inset outline и hover/press feedback.

## Следующий шаг

- Если будет дорабатываться остальной `Content Bot`, держать этот блок как визуальный шаблон для остальных live controls, а не возвращаться к маленьким текстовым кнопкам.
