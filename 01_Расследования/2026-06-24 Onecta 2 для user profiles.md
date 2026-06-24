# 2026-06-24 Onecta 2 для user profiles

## Симптом

Оффер `Onecta #2` был доступен только в owner-scoped конфиге `admin`, но не отображался у пользователей роли `user`.

## Зона системы

- PostgreSQL `control_user_app_configs.config_json.offer_mapping`
- таблица `users`
- Autolead UI `/api/offers`

## Гипотеза

Офферы Autolead хранятся не в embedded TrafficHub таблице `offers`, а в `control_user_app_configs` внутри `config_json.offer_mapping`. Поэтому добавлять оффер нужно в конфиги конкретных пользователей.

## Проверка

`offers` в embedded TrafficHub DB пустая. Live `control_user_app_configs` показал:

- `admin` имел `Onecta #2`;
- `alex`, `artem`, `kursmerkusheva@gmail.com`, `sergkuz2190` роли `user` не имели `Onecta #2`.

## Наблюдение

Canonical запись взята из `admin`:

```json
{
  "name": "Onecta #2",
  "enabled": false,
  "platform": "lovko",
  "target_url": "https://tracking.lovko.pro/L6eTlM",
  "daily_limit": null,
  "vacancy_ids": [54257329],
  "vacancy_names": []
}
```

Запись добавлена всем текущим активным пользователям роли `user`:

- `alex`;
- `artem`;
- `kursmerkusheva@gmail.com`;
- `sergkuz2190`.

## Вывод

`Onecta #2` теперь доступен всем текущим пользователям роли `user`. Оффер добавлен выключенным (`enabled=false`), чтобы не менять рабочую рассылку без явного действия пользователя.

## Следующий шаг

Если нужно, чтобы все новые пользователи автоматически получали `Onecta #2`, надо отдельно менять default profile provisioning в `services/leads_service.py` / license-control flow. Текущая операция была runtime-data migration для существующих пользователей.

