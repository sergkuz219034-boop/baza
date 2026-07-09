# Готовность Windows setup для локальной версии

## Симптом

Нужно определить, можно ли выдавать текущий `SetupTrafficHub.exe` пользователям как актуальную локальную версию.

## Зона системы

- `.github/workflows/release.yml`
- `tools/windows_installer/build_setup.ps1`
- `tools/windows_installer/SetupTrafficHubInstaller.cs`
- `tools/windows_launcher/TrafficHubLauncher.cs`
- `tools/windows_launcher/TrafficHubUpdater.cs`
- GitHub Release `1.26`
- public endpoint `/download/SetupTrafficHub.exe`

Связанные страницы: [[05_Эксплуатация/Развёртывание]], [[02_Архитектура/Обзор системы]].

## Гипотеза

Опубликованный setup может быть структурно исправен, но не готов к эксплуатации после накопившихся изменений в `main`.

## Проверка

На live repo `/root/TrafficHub`, commit `9d31b608b`, проверены:

- release workflow и исходники C# launcher/installer/updater;
- GitHub Release `1.26` и его workflow;
- состав ZIP release;
- public download и SHA-256;
- Authenticode-подпись setup;
- расстояние `1.26..main`;
- локальные auth/license/bind-тесты;
- update path установленной release-копии.

## Наблюдение

Подтверждено:

- Release `1.26` опубликован `2026-07-02`; build workflow завершился успешно.
- `SetupTrafficHub.exe` доступен через `/download/SetupTrafficHub.exe`, размер `1 899 520` байт, SHA-256 `77436aed2915bcc0ed8241d93ac0d8f1519bc11cb04345898ff923eed62f52ef`.
- ZIP содержит `TrafficHub.exe`, `update.exe`, `ActivateLicense.exe`, `AccountManager.exe`, `main.py`, `requirements.txt`; `.env`, БД, логи и `secrets` не попали в payload.
- Исходники четырёх Windows launcher-бинарников собираются CI; соответствующий CI на текущем `main` зелёный.
- 20 тестов local bind/auth/license прошли.
- Dashboard локального launcher привязан к `127.0.0.1:8080`.
- Setup не имеет Authenticode-подписи: Windows вернул `NotSigned`.
- Между tag `1.26` и текущим `main` 47 коммитов. В release отсутствуют последующие исправления полного цикла, Зарплата.ру, Google Sheets и заполнения форм.
- Packaging исключает `.git`. `TrafficHubLauncher.ManualGitUpdate()` прямо отказывается обновлять копию без `.git`.
- `TrafficHubUpdater` также требует Git, branch и `origin`. Следовательно, кнопка обновления не компенсирует устаревший release.
- Первый запуск требует заранее установленный Python; launcher рекомендует Python 3.12 x64, создаёт `.venv`, устанавливает `requirements.txt` и Playwright Chromium через интернет.
- Полный end-to-end smoke на чистой Windows VM не автоматизирован и в рамках проверки не подтверждён.

## Вывод

Текущий setup пригоден для внутреннего контролируемого теста, но не готов как актуальный production-релиз для пользователей.

Оценка готовности: `55–60%`.

Блокеры выпуска:

1. Собрать новый tag из текущего `main`.
2. Определить рабочую модель обновления release-копии без `.git`: скачивание подписанного release/payload, а не `git fetch`.
3. Добавить Authenticode-подпись и timestamp.
4. Провести clean Windows VM smoke: install → first setup → activation → login → local dashboard → Playwright → restart → update → uninstall/upgrade.
5. Добавить release smoke в GitHub Actions или отдельный Windows test harness.

## Следующий шаг

Сначала исправить release updater и добавить автоматический smoke установленного payload. После этого выпустить новый tag и заменить runtime-копию `data/releases/SetupTrafficHub.exe`.
