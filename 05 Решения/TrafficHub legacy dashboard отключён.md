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

Второе закреплённое решение: `crm-*` hash routes не должны открывать Autolead tab-pane. Для TrafficHub в `dashboard/index.html` и `dashboard/app.js` заведены отдельные внутренние tab-pane:

- `crm-overview`
- `crm-leads`
- `crm-messengers`
- `crm-funnels`
- `crm-networks`
- `crm-finance`
- `crm-analytics`
- `crm-settings`

Эти вкладки читают данные через `/traffic-api/*` и не подменяются разделами `leads`, `offers`, `stats`, `settings` из Autolead-контура.

## Последствия
Пользователь остаётся в одном dashboard. Старый `/traffic/*` не открывается при кликах и прямых ссылках.

Admin видит TrafficHub как отдельный раздел внутри основного dashboard. Обычный `user` по-прежнему не получает доступ к CRM-поверхности.

Код нового UI-блока должен оставаться в основном dashboard. Если потребуется дорабатывать `Воронки`, `Мессенджеры`, `Партнёрские сети`, `Финансы`, `Аналитику` или `Настройки`, нужно расширять соответствующий `crm-*` tab-pane, а не возвращать legacy SPA.

## Альтернативы
Оставить `/traffic/*` как отдельный app-shell. Отклонено: это сохраняет два dashboard и повторяет исходную проблему.

Переиспользовать существующие Autolead tabs для CRM. Отклонено после live-проверки: названия пунктов меню и фактическое содержимое расходятся, что ломает операторскую модель.
