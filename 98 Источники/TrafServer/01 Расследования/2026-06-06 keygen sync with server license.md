# 2026-06-06 keygen sync with server license

## Симптом

Нужно было синхронизировать локальный `LicenseKeygen.exe` из `Desktop.rar` с текущей серверной схемой лицензирования.

## Зона

- `Desktop.rar`
- `tools/windows_launcher/LicenseKeygenLauncher.cs`
- `tools/license_key_security.py`
- `wiki/components/license-activation.md`

## Проверка

1. Распакован `Desktop.rar` через Windows Shell namespace.
2. Внутри найдены:
   - `LicenseKeygen.exe`
   - `license_keygen.settings.json`
3. На сервере прочитаны:
   - `tools/license_key_security.py`
   - `tools/windows_launcher/LicenseKeygenLauncher.cs`
   - `tools/windows_installer/build_setup.ps1`
4. Подтверждено, что канонический Windows keygen собирается именно из `tools/windows_launcher/LicenseKeygenLauncher.cs`.

## Наблюдение

- Серверная схема лицензии использует формат `TH1.payload.signature`.
- Проверка подписи выполняется в `tools/license_key_security.py`.
- Текущий GUI keygen на сервере:
  - встроенно знает приватный RSA-ключ;
  - использует PIN;
  - генерирует payload под текущий activation flow;
  - собирается как `LicenseKeygen.exe` через `build_setup.ps1`.

## Что сделано

- С сервера скачаны:
  - `tools/windows_launcher/LicenseKeygenLauncher.cs`
  - `dashboard/license-keygen.ico`
- Локально собран новый `LicenseKeygen.exe` через `csc.exe`.
- Новый бинарник подложен в распакованный набор:
  - `C:\Users\Арт\Desktop\TrafServer\_tmp_desktop_rar\LicenseKeygen.exe`

## Ограничение

В текущей сессии не было утилиты для пересборки `.rar`, поэтому синхронизирован сам бинарник и распакованная структура, но исходный `Desktop.rar` не был перепакован обратно в RAR-формат.

## Вывод

Канонический keygen теперь собран из текущего серверного исходника. Если понадобится именно обновлённый архив `Desktop.rar`, нужно дополнительно перепаковать содержимое внешним RAR-архиватором.
