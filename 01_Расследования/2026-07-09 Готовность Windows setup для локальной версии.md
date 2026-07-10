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

Дополнение `2026-07-10`:

- Product commit `e122a5290` добавил release-based updater для установленной Windows-копии без `.git`.
- Backend теперь отдаёт portable payload через `/download/TrafficHub-windows-x64.zip`; endpoint выбирает generic `TrafficHub-windows-x64.zip` или свежий `TrafficHub-*-windows-x64.zip` в `data/releases`.
- Product commit `0aa20b897` исправил startup regression: `traffic_hub.migrations.run_migrations()` снова является async-контрактом и корректно ожидается из `traffic_hub/app.py`.
- GitHub Actions для `e122a5290` и `0aa20b897` зелёные: `CI` и `Build and Push Docker Image`.
- Release tag `1.27` собран workflow `Build and Release Windows App` из commit `0aa20b897`.
- Live `data/releases` обновлён:
  - `SetupTrafficHub.exe`, `1 934 848` bytes, SHA-256 `ca06cb9ad4ba7238f913f9e40589284e6d835b7202984028d31ad4cdd09c81be`;
  - `TrafficHub-1.27-windows-x64.zip`, `1 886 605` bytes, SHA-256 `90385e35182b5e84853659b663d348de827532c8e6a6387a52eb201e3715f5fb`;
  - `TrafficHub-windows-x64.zip` указывает на тот же payload.
- Публичные endpoints `https://traffic-hub.pro/download/SetupTrafficHub.exe` и `https://traffic-hub.pro/download/TrafficHub-windows-x64.zip` возвращают `200`.
- Zip payload `1.27`: `720` файлов, обязательные `TrafficHub.exe`, `update.exe`, `ActivateLicense.exe`, `AccountManager.exe`, `main.py`, `requirements.txt` присутствуют; `.git`, `.env`, `data`, `secrets`, БД и логи отсутствуют.
- Новый `SetupTrafficHub.exe` всё ещё `NotSigned` по Authenticode.

## Вывод

После `2026-07-10` setup пригоден для внутреннего контролируемого теста как актуальный `1.27`, но ещё не готов как публичный production-релиз для пользователей.

Оценка готовности после `1.27`: `70–75%`.

Оставшиеся блокеры публичного выпуска:

1. Добавить Authenticode-подпись и timestamp.
2. Провести clean Windows VM smoke: install → first setup → activation → login → local dashboard → Playwright → restart → update → uninstall/upgrade.
3. Добавить release smoke в GitHub Actions или отдельный Windows test harness.
4. Убрать риск dirty-context deploy: live rebuild должен идти из clean `git archive HEAD`, а не из грязного `/root/TrafficHub`.

## Следующий шаг

Сначала пройти clean Windows VM smoke для `1.27` и добавить подпись. После этого закрепить clean-archive deploy как стандартный playbook для live rebuild.
