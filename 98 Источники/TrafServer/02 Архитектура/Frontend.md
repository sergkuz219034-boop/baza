# Frontend

Теги: #архитектура

## Что подтверждено

- `main.py` запускает web dashboard через импорт `api.server`.
- `AccountManager/api/main.py` раздаёт static dashboard из `dashboard/index.html`.
- Для HTML-запросов `AccountManager` умеет делать redirect на основной login.
- В локальном snapshot для `AccountManager` теперь есть базовая dashboard-страница как entrypoint для нового backend scaffold.
- У `AccountManager` теперь есть отдельные frontend-модули `dashboard/js/telegram.js`, `google.js`, `social.js` и `dashboard/css/app.css`.
- Для Google flow есть отдельное browser extension в `chrome-extension/`.

## Что не подтверждено

- В текущем workspace нет полного исходника dashboard frontend.
- Нет полного набора static-ресурсов основного dashboard.
- Нет полного router/source inventory для UI-связанных API экранов.

## Практический вывод

Frontend-контур нельзя документировать как полноценный SPA по этому workspace. Канонично можно утверждать только:

- есть как минимум один основной dashboard;
- есть отдельный static dashboard у AccountManager;
- UI tightly coupled с backend API и auth middleware.

## Смежные страницы

- [[Backend]]
- [[Authentication]]
- [[Known Issues]]
