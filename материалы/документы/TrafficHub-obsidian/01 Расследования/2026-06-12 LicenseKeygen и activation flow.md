# LicenseKeygen и activation flow

## Симптом
- В `LicenseKeygen` администратор вводил логин заранее.
- На странице `/register` пользователь тоже вводит логин сам.
- Отдельный `license_server` выпускал `TH1`-ключи с `login` и `role`, но без `password`, тогда как activation flow в основном сервере ожидает ключ, из которого можно восстановить пароль.

## Зона системы
- Генератор: `LicenseKeygen.cs`.
- License API: `license_server/app.py`.
- Сервер активации: `artifacts/remote_edit/api/server.py` (`/register`, `_apply_activate_license_key`).

## Гипотеза
- Дублирование логина между keygen и `/register` лишнее.
- Для совместимости keygen должен выпускать ключ без обязательного `login`, но с серверно-сгенерированным `password` внутри payload.

## Проверка
- Проверен `license_server/app.py`: до правки `LicenseCreateRequest.login` был обязательным, а `_payload(...)` не содержал `password`.
- Проверен `artifacts/remote_edit/api/server.py`: `_apply_activate_license_key(...)` допускает отсутствие `login`, если он пришёл из формы, но обязательно требует `password` в payload.
- Проверены сборки:
  - `python -m py_compile license_server/app.py`
  - `dotnet build .\LicenseKeygen.csproj -c Release`

## Наблюдение
- Канонический runtime активации уже умеет брать логин из HTML-формы `/register`.
- Несовместимость была не в форме, а в контракте генерации ключа: `license_server` не добавлял `password`.
- `LicenseKeygen` может безопасно выпускать generic activation key по роли, без привязки к логину.
- Дополнительное runtime-расхождение: удалённый `license-api` может ещё жить на старом контракте и отклонять пустой `login` с ошибкой `string_too_short`.
- Для обратной совместимости `LicenseKeygen` теперь отправляет технический placeholder `pending_<role>_<utcstamp>`, если логин не задан в UI. На `/register` этот логин переопределяется реальным логином пользователя.

## Вывод
- Логин нужно убрать из UI `LicenseKeygen`, а не из `/register`.
- Контракт `license_server /keys/create` должен поддерживать пустой `login` и всегда включать `password` в signed payload.
- Пока production `license-api` не обновлён гарантированно, клиенту нужен compatibility fallback с placeholder-логином.

## Следующий шаг
- Если нужно убрать ввод логина и на `/register`, придётся менять уже основной auth-flow: либо читать `login` из ключа всегда, либо вводить отдельный onboarding после активации.
