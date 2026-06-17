# 2026-06-04 accountmanager backend scaffold

Теги: #решение

## Контекст

ТЗ на Account Manager требовало три новых модуля подключения аккаунтов, но локальный snapshot содержал только `AccountManager/api/main.py` без зависимых пакетов.

## Решение

Собран минимально самодостаточный backend scaffold для AccountManager:

- `config.py`
- `database/*`
- `services/*`
- `api/routers/*`
- `dashboard/index.html`

и новые роутеры подключены в `api/main.py`.

На следующем шаге scaffold был расширен до полного vertical slice:

- frontend dashboard c JS/CSS;
- `chrome-extension/*` для Google export;
- `scheduler.py` для фоновых проверок;
- live-ready optional flows для Telethon и Playwright с fallback mode.

## Почему так

- без этого snapshot не может подняться даже на уровне импортов;
- это создаёт рабочую основу для дальнейшей live-интеграции Telethon, Chrome extension и Playwright.

## Последствия

- Account Manager теперь ближе к runnable snapshot;
- Google import/check и CRUD-поверхности формализованы;
- Telegram и social OAuth могут идти по live-path при наличии окружения, но при его отсутствии не ломают сервис и возвращают предсказуемый fallback.

## Связанные заметки

- [[2026-06-04 accountmanager accounts module]]
- [[AccountManager backend scaffold]]
- [[Architecture]]
