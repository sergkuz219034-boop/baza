# БАГ-017: Settings cleanup и debug-файлы

Статус: решено  
Дата: 2026-06-19  
Зона: `dashboard/index.html`, `api/routers/settings_maintenance.py`, `autolead_server_bot`

## Симптом

В настройках TrafficHub в блоке управления данными было много кнопок точечной очистки внутренних таблиц. Нужно было оставить только:

- `Дебаг файлы`;
- `Очистить всю базу данных`.

## Проверка

- На live-сервере проверен блок `Управление данными` в `/root/TrafficHub/dashboard/index.html`.
- Проверен endpoint `/api/settings/db/screenshots` в `/root/TrafficHub/api/routers/settings_maintenance.py`.
- Подтверждено, что приложение в контейнере не использует bind mount исходников: для применения HTML/Python правок нужен rebuild образа.

## Решение

- Из UI удалены кнопки очистки отдельных таблиц: лиды, история рассылок, история приглашений, очередь повторов, логи запусков, автоподбор.
- Кнопка `Debug скриншоты` переименована в `Дебаг файлы`.
- Очистка debug-файлов расширена на:
  - `debug_*.html`;
  - `debug_*.png`;
  - `debug_*.jpg`;
  - `debug_*.jpeg`;
  - `debug_*.webp`.
- Очистка работает в корне runtime, `data` и `data/debug`.

## Проверка после фикса

- `docker compose up -d --build autolead_bot`
- `pytest -q tests/test_settings_maintenance.py`
- Результат: `3 passed`.
- Live-контейнер `autolead_server_bot` отдаёт кнопку `Дебаг файлы`.
- Повторная очистка после удаления всех debug-файлов возвращает `deleted = 0`; UI теперь пишет `файлов для удаления не найдено`.
- `Системная информация` и GitHub update controls скрыты по умолчанию и показываются только после подтверждения роли `admin`.

## Вывод

Кнопка теперь чистит HTML и изображения после неудачного заполнения анкет. Для подобных UI/backend правок на этом deployment нужен rebuild `autolead_bot`, простой restart не применяет код.
