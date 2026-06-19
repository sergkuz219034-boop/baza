# Очистка debug-файлов

## Назначение

Кнопка `Дебаг файлы` в настройках TrafficHub удаляет debug-артефакты после неудачного заполнения анкет.

## Что удаляется

- `debug_*.html`
- `debug_*.png`
- `debug_*.jpg`
- `debug_*.jpeg`
- `debug_*.webp`

## Где удаляется

- корень runtime приложения;
- `data`;
- `data/debug`.

## Endpoint

`DELETE /api/settings/db/screenshots`

Исторически endpoint назывался `screenshots`, но фактически теперь удаляет debug HTML и изображения.

Если endpoint возвращает `deleted = 0`, это означает, что подходящих debug-файлов уже нет. UI должен показывать `файлов для удаления не найдено`, а не считать это ошибкой.

## Доступ

Блок `Системная информация`, GitHub update controls и управление данными доступны только admin. Admin-only элементы скрыты по умолчанию на CSS уровне и раскрываются frontend'ом только после подтверждения роли `admin`.

## Deployment note

Код dashboard и API находится внутри Docker image. После изменения `dashboard/index.html` или `api/routers/settings_maintenance.py` нужен rebuild:

```bash
docker compose up -d --build autolead_bot
```

Простой `docker restart autolead_server_bot` не применит изменения исходников.
