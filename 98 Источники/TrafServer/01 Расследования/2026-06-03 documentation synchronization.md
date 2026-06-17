# 2026-06-03 documentation synchronization

Теги: #debug #архитектура

## Симптом

Текущая документация смешивает live server observations, старые выводы и частичные локальные зеркала, из-за чего новый инженер не может понять, какие знания подтверждены кодом.

## Зона

- `remote_server_snapshot`
- `remote_files`
- корневые SSH/debug утилиты
- существующая wiki в `05 Решения`

## Гипотеза

Нужен новый канонический слой документации, который прямо отделяет:

- подтверждённое исходниками в workspace;
- ожидаемое по импортам и compose;
- неизвестное из-за неполного snapshot.

## Проверка

- Прочитаны `main.py`, `docker-compose.yml`, `deploy/Caddyfile`.
- Прочитаны `traffic_hub/app.py`, `traffic_hub/models/database.py`, `traffic_hub/api/deps.py`, `ownership.py`.
- Прочитаны `services/leads_service.py`, `utils/database.py`, `utils/control_store.py`, `utils/license.py`.
- Сверены старые архитектурные заметки с текущими файлами.

## Наблюдение

- Workspace действительно хранит не full repo, а набор зеркал и snapshot.
- Часть прежних заметок делает слишком сильные выводы о полноте исходников.
- Часть API и frontend-контуров видна только частично.

## Вывод

Новая документация должна быть честной о границах знания и опираться только на проверяемый код в этом workspace.

## Связанные заметки

- [[Overview]]
- [[Architecture]]
- [[2026-06-03 documentation synchronization audit]]
