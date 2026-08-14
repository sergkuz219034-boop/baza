---
title: 2026-06-30 AccountManager logs tab shows account events
---

# 2026-06-30 AccountManager logs tab shows account events

## Симптом

- Во вкладке `Журнал` `AccountManager` пользователь ожидал последние события аккаунтов, но UI показывал старые gateway `request_logs` с путями вроде `/v1/chat/completions`.

## Зона системы

- `AccountManager` dashboard logs.
- Файлы:
  - `AccountManager/api/routers/dashboard.py`
  - `AccountManager/database/schemas.py`
  - `AccountManager/dashboard/app.js`
  - `AccountManager/dashboard/index.html`

## Гипотеза

- Источник данных для вкладки `Журнал` взят не из account lifecycle, а из legacy-таблицы request routing logs.

## Проверка

- `GET /api/dashboard/logs` раньше возвращал `request_logs`.
- Live `request_logs` содержали в основном старые gateway записи от `2026-05-28`.
- Актуальные account events находились в `accounts` через:
  - `status`
  - `check_result`
  - `last_check_at`
  - `last_used_at`
- Для live TG-аккаунтов были подтверждены свежие события вида `Telethon авторизован ...` от `2026-06-30`.

## Наблюдение

- Старый журнал отражал технические запросы маршрутизации, а не поведение аккаунтов.
- Для операционного контроля аккаунтов полезнее агрегировать события из самих account rows.

## Вывод

- `AccountManager` live/product repo переведён на account-event журнал:
  - `check` по `last_check_at`
  - `usage` по `last_used_at`
  - `created` по `created_at`, если аккаунт ещё не проверялся и не использовался
- UI журнала теперь показывает:
  - время
  - аккаунт
  - событие
  - статус
  - сообщение
- Кнопка искусственной записи demo event удалена из вкладки.

## Следующий шаг

- Если понадобится отдельный экран для gateway/request logs, не смешивать его с account timeline; выводить как отдельную вкладку или debug view.
