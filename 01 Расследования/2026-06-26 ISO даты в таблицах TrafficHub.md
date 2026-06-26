# 2026-06-26 ISO даты в таблицах TrafficHub

## Симптом
В таблице TrafficHub в колонке `Создан` отображалась ISO-строка вида `2026-06-26T09:05:58.857951Z`.

## Зона системы
Dashboard CRM sections: `dashboard/app.js`, функция `loadCrmSection()`, общий formatter `fmtDateTime()`.

## Гипотеза
CRM-таблица выводит `created_at` напрямую, не используя существующий formatter дат.

## Проверка
В `dashboard/app.js` найдено:
- `crm-leads`: `value: r => r.created_at || r.created || CRM_TEXT.dash`;
- `crm-finance`: `value: r => r.created_at || r.paid_at || CRM_TEXT.dash`;
- ниже уже существует `fmtDateTime(value)`, который убирает `T/Z` и форматирует дату через `ru-RU`.

## Наблюдение
Проблема была UI-only: данные API остаются ISO, форматирование должно происходить на клиенте.

## Вывод
Колонки дат в CRM-таблицах должны использовать `fmtDateTime()`.

## Что изменено
- `Создан` в CRM-лидах теперь рендерится через `fmtDateTime(r.created_at || r.created)`.
- `Дата` в CRM-финансах теперь рендерится через `fmtDateTime(r.created_at || r.paid_at)`.
- Live container `traffichub_app` пересобран и проверен как healthy.

## Следующий шаг
Если будут найдены другие таблицы с ISO-датами, подключать тот же formatter, не менять формат хранения в API/БД.
