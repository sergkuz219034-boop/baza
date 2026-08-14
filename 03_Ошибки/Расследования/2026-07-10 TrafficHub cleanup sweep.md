# 2026-07-10 TrafficHub cleanup sweep

## Симптом

- В локальной рабочей папке оставались старые копии UI, архивы, экспорты и вспомогательные приложения.
- На сервере оставались неиспользуемый Hermes image, старые product images и пустые volumes.
- В product repo оставался legacy console-keygen без build/import/call path.

## Проверка

- Канонические контуры сохранены: локальные `wiki`, `ssh`, server repo `/root/TrafficHub`, GitHub `TrafficHub` и `baza`.
- Все текущие compose-контейнеры проверены после очистки; `/api/health` вернул `status=ok`, `control.backend=postgres`.
- `LicenseKeygen.cs` не имел ссылок в CI, installer, imports или runtime; актуальный GUI-источник — `LicenseKeygenLauncher.cs`.

## Выполнено

- Удалён legacy `tools/windows_launcher/LicenseKeygen.cs` и устаревшая строка его исключения из installer.
- Удалены неиспользуемые Docker images Hermes и старые product images.
- Удалены пустые старые volumes `caddy_*` и `work_caddy_*`; рабочие `traffichub_*` volumes не трогались.
- Локально удалены старые HTML-копии, архивы, экспорт телефонов, `node_modules`, старые OS-папки и исторические fix-скрипты.
- Сохранены `wiki`, `ssh`, server-sync wrappers, `AGENTS.md` и актуальный локальный `KEY.exe`.

## Ограничения

- `api/server.py.bak` и незакоммиченные изменения `docker-compose.yml` оставлены без изменений: это чужие незакоммиченные данные, их нельзя удалять без отдельного подтверждения.
- Дубликат SSH-папки `traffichubserver` заблокирован правами OneDrive и не удалён силой, чтобы не повредить ключи; canonical SSH-контур работает из `ssh`.

## Вывод

- Runtime и GitHub product repo очищены только от доказанного мусора; активные данные, secrets, PostgreSQL/Redis volumes и compose-сервисы сохранены.
