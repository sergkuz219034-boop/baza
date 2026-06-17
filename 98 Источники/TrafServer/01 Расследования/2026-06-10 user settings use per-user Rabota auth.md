## Симптом

На странице настроек TrafficHub у роли `user` пропали или выглядели сброшенными блоки Rabota.ru и Service Account. Пользователь видел неполную форму, а после перезагрузки значения не совпадали с ожидаемыми "как раньше".

## Зона

- `api/routers/settings.py`
- `dashboard/index.html`
- `dashboard/app.js`
- `utils/control_store.py`
- `utils/license.py`

## Гипотеза

Проблема не в самом сохранении, а в том, что:

1. frontend скрывал Rabota token / service account блоки через admin-only UI-логику;
2. backend отдавал `api_tokens` из общего `config.json`, хотя реальные Rabota credentials для пользователя уже лежали в per-user auth storage;
3. при сохранении auth часть значений писалась не туда, где их ожидал UI.

## Проверка

1. Проверен live-контур на сервере `/root/TrafficHub`.
2. Сверена логика `GET /api/settings` и `PATCH /api/settings`.
3. Проверены реальные значения `load_user_auth_from_cloud("artem")` и `load_user_auth_from_cloud("alex")` внутри контейнера.
4. Проверен DOM `dashboard/index.html` и логика заполнения полей в `dashboard/app.js`.

## Наблюдение

- Для `artem` в control store есть собственные `rabota_app_id`, `rabota_app_secret`, `rabota_access_token` и `google_sa_json`.
- Для `alex` текущий `config.json` остаётся fallback-источником, а per-user auth живёт отдельно.
- До фикса `GET /api/settings` брал `api_tokens` из общего config fallback, из-за чего UI показывал устаревшее или пустое состояние.
- До фикса Rabota token и Service Account блоки были скрыты `data-admin-only`, хотя логически это личные настройки профиля пользователя.

## Вывод

Корневая причина — смешение двух источников правды:

1. персональные Rabota credentials уже переехали в control store по login;
2. UI и API продолжали вести себя так, будто это admin-only / config-only данные.

## Следующий шаг

- Держать Rabota token / Service Account в per-user control store и показывать их в settings для `user`.
- Не возвращать к старой модели, где личные credentials прятались в общем config или были видны только администратору.
