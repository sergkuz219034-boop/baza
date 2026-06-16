# SuperJob Scraper

Файл: `modules/superjob/scraper.py` (678 строк)

## Механизм

Использует **AdsPower** (CDP protocol) для управления удалённым браузером + Playwright.

## Процесс

1. Подключение к AdsPower через CDP
2. Навигация по SuperJob
3. Сбор кандидатов (scroll + pagination)
4. Дедупликация по URL и телефону
5. Экспорт в legacy sheets

## Особенности

- Требует запущенного AdsPower браузера
- CDP endpoint настраивается в конфиге
- Сложный парсинг HTML через BeautifulSoup

## Связанное

- [[08-DevLog/Lessons|Уроки разработки]]
- [[05-Configuration/Config|Конфигурация]]
