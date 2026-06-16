# Планировщик (Scheduler)

## Механизм

Встроенный планировщик на основе `schedule` library. Работает в фоновом `daemon=True` потоке внутри `services/leads_service.py`.

## Режимы работы

- **manual** — ручной запуск через API.
- **auto** — циклический запуск с интервалом из конфига.

## Типы задач

| Задача | Описание |
|--------|----------|
| `autolead` | Сбор откликов + автоподбор |
| `upload` | Экспорт в Google Sheets |
| `send` | Playwright автозаполнение форм |
| `full-cycle` | Все этапы последовательно |
| `superjob` | Scraping SuperJob |
| `stop` | Прерывание текущей задачи |

## Связанное

- [[01-Architecture/Overview|Архитектура]]
- [[05-Configuration/Config|Конфигурация]]
