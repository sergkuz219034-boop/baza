# TrafficHub legacy dashboard отключён

## Проблема
Пункты меню `TrafficHub` открывали второй интерфейс `/traffic/*`, из-за чего пользователь выходил из основного dashboard.

## Контекст
В проекте одновременно существовали:

- основной dashboard `/#...`;
- legacy React SPA `/traffic/*`.

Это создавало два разных UX-контура и путало навигацию.

## Решение
Legacy route `/traffic/*` больше не отдаёт старый dashboard. Он редиректит в основной dashboard:

- `/traffic` -> `/#crm`
- `/traffic/leads` -> `/#crm-leads`
- `/traffic/funnels` -> `/#crm-funnels`
- `/traffic/networks` -> `/#crm-networks`
- `/traffic/finance` -> `/#crm-finance`
- `/traffic/analytics` -> `/#crm-analytics`
- `/traffic/settings` -> `/#crm-settings`

Frontend `openCrmSection()` теперь вызывает `switchTab(...)`, а не `window.location.assign('/traffic...')`.

## Последствия
Пользователь остаётся в одном dashboard. Старый `/traffic/*` не открывается при кликах и прямых ссылках.

## Альтернативы
Оставить `/traffic/*` как отдельный app-shell. Отклонено: это сохраняет два dashboard и повторяет исходную проблему.

