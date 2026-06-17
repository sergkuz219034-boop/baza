# Control store

Теги: #сущность

## Тип

Модуль / БД

## Где находится

`remote_files/utils/control_store.py`

## Роль в системе

Это основной control plane для лицензий, per-user config и per-user auth payloads. Модуль заменяет Google Sheets как primary source для этих данных, сохраняя миграционную совместимость.

## Важный нюанс

`rabota_app_id`, `rabota_app_secret`, `rabota_access_token`, `rabota_refresh_token` и `google_sa_json` считаются per-user auth payload. Их читает `api/routers/settings.py` при отдаче пользовательских настроек и сохраняет обратно отдельно от общего `config.json`.

## Входы

- login
- user config
- auth payload

## Выходы

- `control.db`
- health summary

## Зависимости

- [[License layer]]
- [[Database]]

## Типовые сбои или риски

- миграции со старой схемы;
- сосуществование HWID и login scoped данных.
