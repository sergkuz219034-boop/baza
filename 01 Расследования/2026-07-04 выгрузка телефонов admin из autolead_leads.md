# 2026-07-04 выгрузка телефонов admin из autolead_leads

## Симптом

Нужно выгрузить полный TXT-список телефонов пользователя `admin` за период `2026-06-01..2026-07-04`, без `+` и апострофов.

## Зона системы

- live repo: `/root/TrafficHub`
- runtime DB: PostgreSQL container `traffichub_postgres`
- таблица: `autolead_leads`
- поля: `owner_username`, `phone`, `lead_date`, `collected_at`

## Гипотеза

Период пользовательского запроса должен фильтроваться по смысловой дате лида `lead_date`, а не по технической дате сохранения `collected_at`.

## Проверка

- Схема подтверждена в `/root/TrafficHub/utils/runtime_store_pg_leads.py`: таблица `autolead_leads` содержит `owner_username`, `phone`, `lead_date`, `collected_at`.
- На live выполнена агрегирующая проверка для `owner_username='admin'`.
- `lead_date` нормализован из форматов `YYYY-MM-DD` и `DD.MM.YYYY`.
- Телефон очищен через `regexp_replace(phone, '[^0-9]', '', 'g')`.

## Наблюдение

- По `lead_date` за `2026-06-01..2026-07-04`: `1319` строк, `1290` уникальных телефонов.
- По `collected_at` за тот же период: `23274` строки, `15018` уникальных телефонов.
- Разница подтверждает, что `collected_at` отражает техническое сохранение/импорт и не подходит для пользовательского периода лидов.

## Вывод

Для выгрузки телефонов за период нужно использовать `lead_date`.
Создан TXT-файл `C:\Users\Арт\Desktop\Project\admin_phones_2026-06-01_2026-07-04_full.txt`: полный список строк из `autolead_leads` для `admin`, только цифры, без `+` и `'`.

## Следующий шаг

Если потребуется список без дублей, выгружать отдельный файл через `SELECT DISTINCT phone_digits`, сохраняя текущий full-list как канон для "полного списка".
