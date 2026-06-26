# SaaS identity без HWID

## Проблема

TrafficHub работает как серверный SaaS: один live-сервер обслуживает нескольких пользователей. Machine-scoped `HWID` не подходит как ключ аккаунта, лицензии или интеграционных секретов.

## Контекст

- Старый контур keygen/activation был ближе к desktop/install-модели.
- В SaaS runtime настройки Google Sheets, Rabota.ru и другие secrets должны быть изолированы по пользователю.
- Ранее уже были инциденты с пересечением настроек между пользователями, поэтому machine/global bootstrap считается опасным.

## Решение

- Аккаунт активируется и обновляется по `login`.
- `HWID` в activation payload игнорируется.
- В `control_license_users.hwid` пишется пустое значение.
- Auth payload сохраняется в user-scoped хранилище через `save_user_auth(login, auth)`.
- Startup sync секретов по server `HWID` отключён.
- Legacy HWID helpers оставлены только как compatibility no-op boundary до отдельной migration cleanup; legacy cloud hooks в `utils/license.py` также no-op.

## Последствия

- Пользовательские настройки не должны зависеть от железа сервера или контейнера.
- Keygen/activator больше не должен просить пользователя прислать HWID.
- Новые пользователи наследуют SaaS-модель автоматически.
- Старые legacy columns/tables можно удалить позже отдельной миграцией, когда будет подтверждено отсутствие внешних зависимостей.

## Альтернативы

- Оставить `HWID` как второй ключ аккаунта: отклонено, потому что это ломает multi-tenant SaaS на одном сервере.
- Привязывать к browser/device fingerprint: отклонено, потому что это не решает server-side secret isolation и усложняет поддержку.
- Мигрировать DB schema сразу с удалением columns: отложено, потому что безопаснее сначала отключить active runtime dependency, затем удалять legacy surface отдельной миграцией.

## Связанные страницы

- [[01_Расследования/2026-06-26 SaaS без HWID]]
- [[02_Архитектура/Обзор системы]]
- [[06_Отладка/Каталог ошибок]]
