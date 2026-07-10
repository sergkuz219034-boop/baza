# 2026-07-10 Short activation key format

## Симптом

`KEY.exe` генерировал длинные activation keys, которые неудобно передавать клиентам.

## Проверка

- Длина RSA-подписи остаётся неизменной; сокращать её означало бы ослабить защиту.
- Основной размер занимал base64-представленный JSON payload.
- Server verifier, `ActivateLicense.exe` и GUI keygen проверены по одному формату.

## Решение

- Новый key format: `TH2.payload.signature`.
- Payload JSON сжимается DEFLATE до подписи.
- Подпись проверяется по сжатым байтам, затем payload распаковывается и передаётся в прежний activation flow.
- `TH1` остаётся совместимым со старыми ключами.
- Новый `KEY.exe` собран локально из server source; keygen не входит в публичные releases.

## Проверка после изменений

- `tests/test_license_key_security.py`: `6 passed`.
- Windows launcher CI: green.
- Live app rebuilt; `/api/health` возвращает `status=ok`.
- Для типового payload base64-часть сократилась примерно с 208 до 156 символов; RSA signature не изменялась.
