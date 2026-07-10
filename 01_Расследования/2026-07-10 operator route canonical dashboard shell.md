# `/operator` использовал отдельный макет вместо каноничного TrafficHub shell

## Симптом

Единственной публичной operator-страницей должен быть поддомен `operator.traffic-hub.pro`: он должен выглядеть как CRM-макет `crm.html`, но использовать боевую operator-авторизацию и отдельную operator-навигацию. Старый путь `traffic-hub.pro/operator` должен быть удалён.

## Зона системы

- live `/root/TrafficHub/api/server.py`
- `dashboard/operator.html`
- CRM-style operator shell: `dashboard/operator.html`
- reference mockup: `crm.html` из пользовательского вложения
- internal route `GET /operator-host`
- public host `operator.traffic-hub.pro`

## Гипотеза

Дублированный operator frontend появился как быстрый отдельный экран и перестал соответствовать общему TrafficHub auth/session, навигации и ограничениям роли.

## Проверка

- `dashboard/operator.html` заменён на CRM-style разметку из пользовательского макета.
- Тестовый `VALID_KEY=PRO2026` удалён; форма вызывает `/auth/operator-login`, а при открытии проверяет `/auth/session`.
- Вкладки operator shell соответствуют CRM-макету: `Сводка`, `Кандидаты`, `Вакансии`, `Источники`, `Учебные материалы`, `Статистика`, `Настройки`.
- Caddy получил отдельный блок `operator.traffic-hub.pro`, который проксирует корень поддомена во внутренний `/operator-host`.
- Старый `GET /operator` проверен: `404`.
- DNS `operator.traffic-hub.pro` разрешается в `150.241.70.31`; Caddy успешно получил публичный сертификат.
- Live `https://traffic-hub.pro/operator` отвечает `200`; `/api/health` отвечает `{"status":"ok"}`.

## Наблюдение

Проблема была в смешении демонстрационного макета и production auth. После переноса визуального shell тестовая auth-логика удалена, но содержимое вкладок `crm.html` пока является UI-каркасом и требует отдельного подключения реальных operator API-read-моделей.

## Вывод

`operator.traffic-hub.pro` отдаёт CRM-style operator shell. Авторизация проходит через боевой `/auth/operator-login`; старый путь `/operator` недоступен.

## Следующий шаг

Добавить реальные API-загрузчики для KPI, кандидатов и вкладок, затем проверить UI smoke в браузере. После публикации DNS проверить HTTPS и сертификат поддомена.

Подтверждение: product commit `0a2c1e217` и последующий route-fix, live rebuild выполнен, DNS/TLS проверены; wiki commit `34429b1` синхронизирован в `baza`.
