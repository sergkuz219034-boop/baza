# Уроки разработки

Источник: `tasks/lessons.md`

## SuperJob Scraping

- AdsPower CDP — нестабильное соединение, требуется retry logic
- SuperJob меняет HTML-структуру — нужна гибкая парсинг-логика
- Rate limiting — необходимо соблюдать паузы между запросами

## Playwright

- Headless Chromium детектится — нужны anti-detection меры
- Per-lead context изолирует сессии
- Screenshot + HTML diagnostics критичны для отладки

## База данных

- Три БД вместо одной — сложнее синхронизация, но выше изоляция
- `control_sync_queue` — фоновая синхронизация между autolead.db и control.db

## Связанное

- [[02-Modules/SuperJob|SuperJob Scraper]]
- [[02-Modules/VbivBot|Playwright Vbiv Bot]]
- [[04-Database/Schema|Схема БД]]
