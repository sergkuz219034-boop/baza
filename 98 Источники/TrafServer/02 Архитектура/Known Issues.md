# Known Issues

Теги: #архитектура

## Подтверждённые проблемы документации и кода

- Workspace неполный и не позволяет восстановить весь repo на 100%.
- `main.py` ссылается на `api.server`, которого нет в snapshot.
- `traffic_hub/app.py` импортирует роутеры, исходники которых отсутствуют в зеркале.
- Security surface распределён между `.env`, PostgreSQL control store, `data/runtime/secrets/`, системным `secrets/` и legacy compatibility-слоем.
- `AccountManager` backend scaffold восстановлен локально, но full live automation для Telethon и Playwright в snapshot всё ещё неполная.
- Google extension и browser automation рассчитаны на локальный loopback-сценарий и требуют отдельной operational проверки в реальной среде браузера.
- Часть старых заметок и legacy config payload всё ещё может ссылаться на `secrets/config.json` и `secrets/service_account.json`, хотя канонический runtime-path уже другой.

## Архитектурные спорные места

- несколько auth boundary в одном compose;
- несколько БД и ownership-моделей;
- сохранённый legacy-код ради миграции повышает сложность сопровождения.
- compatibility layer для старых runtime-secret путей пока нужен, потому что не все исторические payload автоматически переписаны.

## Смежные страницы

- [[Security]]
- [[Deployment]]
- [[2026-06-03 documentation synchronization audit]]
