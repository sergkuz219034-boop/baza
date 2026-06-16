# Windows Setup

## Launcher

`TrafficHub.exe` — C# WinForms приложение, которое:
1. Находит/создаёт `.venv`
2. Устанавливает зависимости
3. Устанавливает Playwright Chromium
4. Запускает `main.py`

## Компиляция (CI)

```bash
csc -target:winexe -out:TrafficHub.exe TrafficHubLauncher.cs
```

## Инсталлятор

`SetupTrafficHub.exe` — собирается скриптом:
```
tools\windows_installer\build_setup.ps1
```

## Сборка релиза (GitHub Actions)

Работа workflow `release.yml`:
1. Компиляция C# launcher
2. Сборка `SetupTrafficHub.exe`
3. Сборка portable ZIP
4. Публикация GitHub Release

## Связанное

- [[06-Deployment/Docker|Docker]]
- [[06-Deployment/AccountManager|AccountManager]]
