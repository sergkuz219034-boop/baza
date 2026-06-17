Проблема

- Логи и Google Sheets auth/config частично нарушали tenant isolation.

Контекст

- In-memory WebSocket логи уже были owner-scoped.
- API истории логов подмешивал общий file-fallback.
- `service_account.json` сохранялся как общий файл.
- User-config мог наследовать общие Google Sheets ids и путь к service account.

Решение

- В `/api/logs` чтение переведено на owner-scoped `app_log` с привязкой к текущему пользователю, а live `ws_manager` используется как дополнительный источник для свежих событий.
- Добавлена owner-scoped таблица `app_log` в локальной SQLite для постоянной истории UI-логов.
- `WebSocketLogHandler`/`WSManager` сохраняют owner-scoped log messages в `app_log`, а `GET /api/logs` объединяет persistent history и live recent logs.
- `DELETE /api/logs` очищает и persistent `app_log`, и live in-memory cache, поэтому кнопка очистки теперь работает после reload.
- Загрузка Google service account переведена на owner-scoped путь `service_account__<username>.json`.
- Для user-config прекращено наследование общих Google Sheets ids и `service_account_file` из fallback.
- Для существующего пользователя `artem` выполнена миграция на owner-scoped SA-файл.
- Для `alex` общие Google Sheets поля очищены, так как собственного `google_sa_json` в control store не было.

Последствия

- После рестарта история логов остаётся доступной через persistent `app_log`, а live-лента продолжает дополняться `ws_manager`.
- Пользователь без собственного SA больше не будет молча работать на чужом ключе.
- Для некоторых пользователей понадобится заново загрузить свой Google service account и указать свои таблицы.

Альтернативы

- Хранить полную историю логов в owner-scoped таблице БД и читать её вместо файла.
- Оставить file-fallback, но писать owner-метку в каждый лог на диск и фильтровать при чтении.
