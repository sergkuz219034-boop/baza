# Audience Parser dropdown и layout

## Симптом

Во вкладке Telegram Audience Parser список аккаунтов отображался как узкая пустая кнопка со стрелкой. Поля рассылки, подписи и кнопки выстраивались одной плохо читаемой строкой.

## Зона системы

- `AccountManager/dashboard/index.html`
- `AccountManager/dashboard/style.css`
- `AccountManager/dashboard/js/audience_parser.js`
- `AccountManager/api/routers/audience_parser.py`
- `AccountManager/services/audience_parser_service.py`
- контейнер `traffichub_account_manager`

## Гипотеза

Frontend и backend Audience Parser развернуты несинхронно, а форма не имеет явной grid-структуры и размеров контролов.

## Проверка

- В server worktree frontend уже ссылался на `/api/audience-parser/accounts`, но router/service оставались untracked и отсутствовали внутри live container.
- `select` не имел собственной ширины; подписи формы были непосредственными grid-элементами без колонок.
- После сборки проверены backend `safe_accounts`, статические файлы внутри image, public health и GitHub checks.

## Наблюдение

- Product commit `f8cad38fb` завершил Audience Parser как единый релиз: router, service, JS, DOM, CSS и regression-тесты.
- Backend в live возвращает `6` доступных Telegram-аккаунтов без `phone`, `api_hash` и `session_string`.
- Нативный `select` занимает полную ширину, до загрузки явно disabled, после загрузки содержит аккаунты и становится активным.
- Блоки разделены на понятные шаги, поля рассылки собраны в двухколоночную сетку с mobile fallback, действия вынесены в отдельную строку.
- Cache-buster: `20260715-audience-ui-v2`; контейнер healthy.
- В ходе smoke обнаружен startup-лог полного PostgreSQL URL. Commit `fa87b0e4b` заменил его на безопасный `db_backend=postgresql` и добавил regression-тест.

## Вывод

Пустой dropdown был deployment drift, а визуальный дефект — отсутствием явных layout constraints. Оба дефекта устранены; backend и frontend теперь поставляются одним коммитом.

## Следующий шаг

Необходимость ротации PostgreSQL credential оценить отдельно: до фикса полный URL попадал в локальный container log. Новые startup-события секрет не печатают.

