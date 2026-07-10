# 2026-07-10 Short activation key format

## Симптом

`KEY.exe` генерировал длинные activation keys, которые неудобно передавать клиентам.

## Проверка

- Длина RSA-подписи остаётся неизменной; сокращать её означало бы ослабить защиту.
- Основной размер занимал base64-представленный JSON payload.
- Server verifier, `ActivateLicense.exe` и GUI keygen проверены по одному формату.

## Решение

- Основной формат для новых ключей: `TH3-xxxxxxxxxxxxxxxx` - серверный код длиной 20 символов.
- `KEY.exe` сначала создаёт подписанный `TH2.payload.signature`, затем передаёт его на `POST https://traffic-hub.pro/license/shorten`.
- `license_server` проверяет подпись, сохраняет связку `TH3 -> TH2` в PostgreSQL (`license_short_keys`) и возвращает короткий код.
- При активации приложение и Operator CRM получают исходный `TH2` через `GET /license/resolve/{TH3}`, после чего повторно проверяют подпись локально. Короткий код не заменяет криптографическую проверку.
- Для активации `TH3` требуется доступ к `traffic-hub.pro`. Если выдача короткого кода в keygen недоступна, он оставляет полный `TH2` вместо создания невалидного ключа.
- `TH1` и `TH2` остаются совместимыми со старыми и офлайн-сценариями.
- Новый `KEY.exe` собран локально из server source; keygen не входит в публичные releases.

## Проверка после изменений

- `tests/test_license_key_security.py` и `tests/test_activate_license.py`: `9 passed`.
- Live-проверка: `TH3-Xck3fwBFzRqMLnEW` (тестовый код) раскрылся в исходный `TH2`; основной verifier подтвердил login и роль `operator`.
- Длина проверенного тестового `TH2`: 581 символ, `TH3`: 20 символов.
- Live app rebuilt; `/api/health` возвращает `status=ok`.
