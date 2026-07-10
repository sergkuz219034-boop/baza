# `/operator` использовал отдельный макет вместо каноничного TrafficHub shell

## Симптом

Страница `/operator` и будущий поддомен `operator.traffic-hub.pro` должны выглядеть как CRM-макет `crm.html`, но использовать боевую operator-авторизацию и отдельную operator-навигацию. На live одновременно существовал отдельный макет с тестовым брендом `CadryPRO` и тестовой формой активации.

## Зона системы

- live `/root/TrafficHub/api/server.py`
- `dashboard/operator.html`
- CRM-style operator shell: `dashboard/operator.html`
- reference mockup: `crm.html` из пользовательского вложения
- route `GET /operator`

## Гипотеза

Дублированный operator frontend появился как быстрый отдельный экран и перестал соответствовать общему TrafficHub auth/session, навигации и ограничениям роли.

## Проверка

- `dashboard/operator.html` заменён на CRM-style разметку из пользовательского макета.
- Тестовый `VALID_KEY=PRO2026` удалён; форма вызывает `/auth/operator-login`, а при открытии проверяет `/auth/session`.
- Вкладки operator shell соответствуют CRM-макету: `Сводка`, `Кандидаты`, `Вакансии`, `Источники`, `Учебные материалы`, `Статистика`, `Настройки`.
- Caddy получил отдельный блок `operator.traffic-hub.pro`, который проксирует корень поддомена в `/operator`.
- DNS `operator.traffic-hub.pro` на момент проверки не разрешается, поэтому внешний TLS ещё не может быть подтверждён.
- Live `https://traffic-hub.pro/operator` отвечает `200`; `/api/health` отвечает `{"status":"ok"}`.

## Наблюдение

Проблема была в смешении демонстрационного макета и production auth. После переноса визуального shell тестовая auth-логика удалена, но содержимое вкладок `crm.html` пока является UI-каркасом и требует отдельного подключения реальных operator API-read-моделей.

## Вывод

`/operator` сохранён как отдельная ссылка и отдаёт CRM-style operator shell. Авторизация проходит через боевой `/auth/operator-login`; Caddy готов к `operator.traffic-hub.pro` после добавления DNS A-записи.

## Следующий шаг

Добавить реальные API-загрузчики для KPI, кандидатов и вкладок, затем проверить UI smoke в браузере. После публикации DNS проверить HTTPS и сертификат поддомена.

Подтверждение: product commit `e28db2dab`, GitHub Actions `success`, live rebuild выполнен.
