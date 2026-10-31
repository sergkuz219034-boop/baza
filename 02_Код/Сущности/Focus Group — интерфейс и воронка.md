# Focus Group — интерфейс и воронка

## 2026-10-26 — отдельный публичный лендинг услуг

По текущему запросу владельца создана версия 3.0 отдельного статического лендинга «Фокус Групп» в Codex Sites: маркетинг, ИИ-автоматизации, построение отдела продаж и найм сотрудников. Сохранены персональная подача и контакт @sergkuz2190. По явному разрешению владельца access_mode=public, revision 2; deployment succeeded и публичный режим подтверждены штатными инструментами Sites. Адрес: https://focus-grupp-marketing.stablering1.chatgpt.site.

По указанию «стиль и рисунки как у TrafficHub» использованы проверенные локальные гравюры `outputs/all-engravings-20261005/hero-hermes-cutout-v2.png`, `agent-engraving.webp`, нейтральный графит и Inter; знак «Фокус Групп» сохранён. Цены, клиентские кейсы, отзывы и показатели не выдуманы. Исходники: `C:/Users/admin/Documents/Codex/2026-10-25/referenced-chatgpt-conversation-this-is-an/work/focus-grupp-landing`, commit `d22262db5335b3f354e70737726bc79f34b14d36`.

Целевые статические проверки и 7 проверок формы PASS. Живой browser desktop/mobile, Core Web Vitals и фактическая отправка Telegram не проверены из-за предшествовавшего отказа браузерного доступа; отказ не обходился. Evidence: `C:/Users/admin/Documents/Codex/2026-10-25/referenced-chatgpt-conversation-this-is-an/outputs/focus-grupp-v3-release.md`, архив `focus-grupp-v3.zip` рядом. Область изменения — этот отдельный лендинг Codex Sites.

Проверено: 2026-10-04. Источник — свежий серверный снимок `/opt/focus-group`, сохранённый в `C:/Users/admin/Desktop/Project/outputs/focus-group-audit-20261004/source/`.

Публичная анкета находится в `static/lead-form.html` и `static/lead-form.js`; вводный маршрут — в `static/onboarding/`; рабочий SPA — `static/index.html`, `static/app.js`, `static/hr-ui.js`, `static/crm-ui.js`, `static/kanban-ui.js`. В SPA объявлены роли `ADMIN`, `CURATOR`, `SOCIAL_ADMIN`, `LEAD_OPERATOR`, `SALES_MANAGER`, `CANDIDATE` (`static/app.js:3–4`).

Кодовый аудит обнаружил потерю фокуса и подстановку тире в двух канбан-поисках, отсутствие интерфейса поиска отказанных/резервных/заблокированных кандидатов, гонку ответов при открытии лидов, отсутствие timeout в SPA API, недоступность переключателя темы до входа и отсутствие accessible names основных диалогов. Подробные точные строки, последствия и границы проверки: `C:/Users/admin/Desktop/Project/outputs/focus-group-audit-20261004/AUDIT.md`.

В анкете согласие на обработку данных не содержит ссылки на политику и идентификации оператора (`source/static/lead-form.html:46`). Это зафиксировано как UX-пробел доверия без юридической квалификации.

Маршрут кандидата также содержит подтверждённые кодом расхождения: кнопка «Посмотреть предложение» вызывает принятие оффера без предварительного показа условий (`source/static/candidate-experience.js:6`, `source/static/app.js:36`); общий onboarding описывает поиск и передачу контактов для всех ролей (`source/static/onboarding/index.html:73,115`); TESTING в SPA показывает ожидание, хотя backend может требовать practical (`source/static/candidate-experience.js:5`, `source/hr_service.py:1943–1954`). Калькулятор использует демонстрационные 12000 ₽ за результат, а реальный оффер строится из compensation_schemes (`source/static/onboarding/js/app.js:131`, `source/hr_service.py:1235–1244`). Это кодовые выводы, не проверка начислений в production БД.

Live публичные экраны и здоровье приложения проверял основной агент; локальный admin проверялся на синтетических данных. Проверка всех авторизованных production ролей не подтверждена. Данные настоящих кандидатов не использовались этой исследовательской подзадачей.

Подготовленный редизайн: `C:/Users/admin/Desktop/Project/outputs/focus-group-audit-20261004/release/static/`. Исходный detector: `detector.json`; detector редизайна: `redesign-detector.json` в том же каталоге. Предупреждения detector требуют проверки computed styles и не равны подтверждённым дефектам. Редизайн развёрнут на RU-сервере и проверен: 11 статических файлов отдаются с ожидаемым содержимым, `/api/health` HTTP 200, контейнер `focus-group-app-1` healthy. Доказательства: `public-checks.json`, `deployment-manifest.json`, `verification.json`, `live-login.jpg` в каталоге аудита. Backup: `/opt/focus-group/backups/minimal-20261004`. Светлая тема стала исходной для новых посетителей, сохранённая тёмная поддерживается. Переключатель доступен до входа; основные диалоги получили accessible names. Публичный вариант роли переименован в «Специалист по работе с клиентами» с сохранением backend value. Прочие кодовые findings не обозначаются исправленными.

Связано: [[00_Главное/Index|Карта базы]], [[00_Главное/Главная/Протокол знаний|Протокол знаний]].

## 2026-10-05 — завершение тёмной темы

По скриншотам пользователя подтверждены светлый HTML canvas и белый details продолжения анкеты. В `static/focus-minimal.css` добавлены тёмные canvas, details/form, линии, спокойные номера этапов, ссылки и error states. Четыре статических файла обновлены; app пересобран, public health HTTP 200. Live браузер подтвердил совпадающий фон html/body rgb(23,28,25), читаемый summary и отсутствие desktop overflow; локально проверены узкая ширина и обратное переключение в светлую тему. Evidence: `C:/Users/admin/Desktop/Project/outputs/focus-group-audit-20261004/dark-deployment.log`, `dark-theme-fixed.jpg`, `dark-theme-detail.jpg`. Backup `/opt/focus-group/backups/dark-theme-20261005/static`.

## 2026-10-05 — исправления оформления

Исправлены просмотр оффера перед принятием, состояния TESTING и ACTIVE, подсказки и повторное открытие реквизитов, тёмный заголовок оформления, пустая задача дней 3–4, итог дня 5, timeout SPA API, канбан-поиск, гонка ответа detail и отображение завершённых кандидатов. Проверка через browser на синтетической SQLite, JS syntax и py_compile. Подробные границы: C:/Users/admin/Desktop/Project/outputs/focus-group-audit-20261004/FLOW-FIXES-20261005.md. Не подтверждены полная responsive матрица, доставка внешних кодов и финальная подпись; утверждённая политика и реквизиты оператора данных остаются необходимыми исходными данными.

Публикация проверена: 9 frontend ресурсов совпадают с итоговыми файлами с учётом штатного добавления version query к lead-form.css. Health HTTP 200, app healthy. Доказательства: flow-public-checks.json и flow-health.log в указанном каталоге.

## 2026-10-05 — публичные реквизиты агентства

По данным владельца добавлены страница /company.html и единый footer публичных экранов. В анкете явно указан оператор данных; на странице есть ссылка проверки в Rusprofile. Email пока не публикуется по ответу пользователя «пока никакой». Политика обработки данных остаётся незавершённой до определения канала обращений и условий. Evidence: C:/Users/admin/Desktop/Project/outputs/focus-group-audit-20261004/COMPANY-20261005.md. Договорные snapshots и данные кандидатов не менялись.

Публикация реквизитов подтверждена: company-public-checks.json — пять ресурсов HTTP 200 и точное совпадение; браузер открыл live /company.html с реквизитами, company-live.jpg.

## 2026-10-05 — векторная концепция логотипа FG

Создана новая монограмма FG: кольцевой контур G и геометрическая F, forest/ivory палитра. Артефакты C:/Users/admin/Desktop/Project/outputs/focus-group-audit-20261004/logo-v2/: focus-logo.svg, focus-logo-dark.svg, варианты знака и reference.png. SVG содержат только векторную геометрию; надписи переведены в кривые, внешние шрифты и растровые вложения отсутствуют (проверено XML parser). Это концепция и референс для пользователя; текущие production assets не заменены.

## 2026-10-05 — новая концепция логотипа Ф

Предыдущая FG отклонена владельцем. После исследования рекомендаций Adobe и поиска плагинов создана одна новая векторная концепция: знак Ф, Georgia в кривых, forest/ivory, отдельный малый знак. Реальные SVG экспортированы resvg; XML проверен, растровых вложений и зависимых надписей нет. Это концепция, production не менялся. Evidence: C:/Users/admin/Desktop/Project/outputs/focus-group-audit-20261004/logo-v3/DESIGN.md, reference.png и verification.json. Юридическая уникальность не проверялась.

## 2026-10-09 — исправление тёмной темы карточек компаний

Вход на RU восстановлен по актуальному файлу пользователя; проверен host fingerprint. В /opt/focus-group/static/focus-minimal.css поверхности company-guide-grid, stop-list, company-example и operator-example переведены на общие --surface/--surface2/--text/--muted. В lead-form.html версия CSS обновлена до 20261009-guide-theme. Пересобран только app, контейнер healthy; SHA256 CSS сервера и контейнера совпадает: 99a26cae6b89471cd3180cb01ddbb382bcca01d1c98d55ab25354c7f278e42fe. Rollback: /opt/focus-group/backups/dark-company-guide-20261009/. В этом серверном каталоге отсутствует Git, поэтому сохранены backup и лог проверки вместо server commit.

Live браузер подтвердил новый stylesheet и fg-dark. Локальная синтетическая карточка с фактическими опубликованными CSS проверена браузером в обеих темах: тёмный фон карточек rgb(32,39,33), текст rgb(182,193,184); светлый фон rgb(255,255,255), текст rgb(92,102,95). Приватный этап анкеты кандидата не открывался и кандидатские данные не создавались. Evidence: C:/Users/admin/Desktop/Project/outputs/focus-dark-20261009/deploy.log, preview.py, dark-preview.png. Доступы хранятся только в .ssh-private/SSH-доступы-актуально.md; этот путь закреплён в правилах ИИ.


## 2026-10-12 — экраны, типографика и иконки

Проверены публичная анкета и оформление; закрытый кандидатский UI на свежем снимке /opt/focus-group с синтетической SQLite. Пройдены четыре шага знакомства, отправка анкеты/ответов/учебного задания; осмотрены реквизиты, договор и пять дней. Полный production-цикл, доставка кодов, подпись и полный responsive coverage не подтверждены. Report с точными границами и findings: C:/Users/admin/Desktop/Project/outputs/focus-screens-20261012/AUDIT.md; галерея 32 представлений gallery.html; styles browser-checks.json, source-manifest.json.

Подтверждены несогласованное публичное название роли, общий контент поиска компаний, технические названия схем оплаты в синтетическом предложении, отсутствие ссылки копирования на просмотренном success, неодинаковые font-family controls, подписи 8–10px и бледный подзаголовок /employment/. Inter указан в CSS, но font asset/@font-face не найден; фактический fallback не определялся. Дни 3–4 требуют связи с куратором без показанного контактного CTA.

По прямому запросу пользователя исправлены иконки и наложение иллюстрации /employment/: корона/ромбы заменены на смысловые SVG, close тоже SVG; accessible names и внешние адреса сохранены. Rebuild/recreate только app. Runtime healthy, /api/health ok=true, одинаковый SHA256 server/container 80a3c6db3a1e1a442b4ac321cdfbee7f58c05af87d794ef2205184bb8ad0a4ec. Доказательства deploy.log, verify.log, icons.diff, 28-icons-live.jpg и 29-guide-live.jpg в указанном каталоге. Rollback /opt/focus-group/backups/icons-20261012/employment.html. Остальные findings остаются открытыми.


## Аудит runtime — 2026-10-12

Проверен RU host и publicFocus:health200,DBquick_checkok,publiclogin/themebrowser без consoleerrors/desktopoverflow; все роли не проверены. Новейшая из21 найденной локальной DBbackup2026-09-28T08:06Z,backupcron/timer не найден; externalcopy неизвестна. HTTPlog_message отключён app.py473–474, Dockerlogs без rotation. Root/passwordSSH разрешён(public22); факт компрометации не установлен. Источники/проверки `C:/Users/admin/Desktop/Project/outputs/all-server-audit-20261012/ru/REPORT.md`, `ru/finalchecks.txt`, `browser-checks.md`. Общая сводка [[03_Ошибки/Расследования/2026-10-07 TrafficHub project audit]].


## Проверенная резервная копия — 2026-10-12

Исправление H3 подготовлено: online SQLite backup API читает live DB в режиме ro, сохраняет атомарную копию и SHA256 manifest с правами 0700/0600. Проверенная копия `/opt/focus-group/backups/verified-sqlite/focus-20261012T080912977089Z/hrcadry.db`; isolated restore quick_check/integrity_check ok, schema и counts совпадают. Данные не выгружались с сервера, production не перезапускался. Код в отдельном private Git `/opt/focus-group-backup-history`, commit `d7ea22793710819b6441209049dca08e5567046a`; synthetic WAL и corrupt-failure checks PASS. Ежедневный timer03:45Europe/Moscow подготовлен, **не установлен и не включён**, ожидает выбора расписания; H3 пока не закрыт полностью. Внешняя защищённая копия отсутствует в проверенном контуре. Точный evidence: `C:/Users/admin/Desktop/Project/outputs/high-server-fixes-20261012/ru-backup/EVIDENCE.md`, `deploy.txt`, `verify.txt`, `schedule.txt`.


### Активация расписания — 2026-10-12

После выбора daily режима основной агент активировал `focus-group-backup.timer`: active/enabled, запуск ежедневно03:45Europe/Moscow, ближайший13октября2026в03:45МСК(00:45UTC). Существующие копии сохранены, удаления/retention не включены. Live public health ok. Доказательства `C:/Users/admin/Desktop/Project/outputs/high-server-fixes-20261012/ru-backup/activate.txt`. Независимая зашифрованная offhost replica ещё готовится; её готовность здесь не заявлена.


### Независимая защищённая копия — 2026-10-12

H3 исправлен в проверенном контуре: daily03:45МСК active/enabled; ручной запуск systemd success. Каждая новая verified копия после создания шифруется GPG и отправляется на origin через отдельный pinned SSH key и receiver с forced-command. Реальная offhost copy `/var/lib/traffichub-offsite-backups/focus-group/focus-group-20261012T082028560877Z.tar.gpg` расшифрована и проверена на origin: DB SHA256, schema,61tablecounts,quick_check/integrity_check совпадают с manifest. Private decrypt key хранится только на origin с root-only доступом; production/исторические копии не менялись. Source history `/opt/focus-group-backup-history`,commit8a5eb76f50d79c0878ff6e18b14e7f3ee468825b. Evidence `C:/Users/admin/Desktop/Project/outputs/high-server-fixes-20261012/ru-backup/EVIDENCE.md`, `enable-replication.txt`, `service-smoke.txt` и `../origin-backup/focusverify-deploycontext.txt`. TrafficHubdaily не включён: его режим отдельно только перед рискованными обновлениями. Защита от одновременной потери двух серверов требует отдельного custody recovery keys.

Полный backup+ExecStartPost offhost цикл проверен через systemd: success2026-10-12в11:29:22МСК, snapshot082921859996Z, timeractive,publichealthok. Evidence `C:/Users/admin/Desktop/Project/outputs/high-server-fixes-20261012/ru-backup/service-smoke-replicated.txt`.


## 2026-10-12 — privacy-safe HTTP диагностика

FocusHTTPjournal теперьevent/method/status/coarserouteonly безrawURL/query/IP/body/headers/errors/кандидатскихID. Fakehandler иlivesyntheticsecretchecksPASS;app rebuilthealthy/public200. Все7RUactivecontainerslogs10m/3,workerimages/runtimepreservedпослеmainidle. Financebackend/TLSHTTPS200 черезresolve,publicDNSNXDOMAIN;userсамдобавляетAfinance→77.91.115.22 TTL300. Необъявлятьfinancepublicготовымдопропагации. Evidence `C:/Users/admin/Desktop/Project/outputs/medium-server-fixes-20261012/ru/EVIDENCE.md`.

## 2026-10-20 — макеты презентаций вакансий

Подготовлены три локальных PDF по 10 страниц на основе приложенного пользователем образца: администратор соцсетей, оператор заявок, менеджер продаж. По прямому разрешению пользователя условия оплаты, график, выплаты и обучение придуманы для последующей замены и явно помечены как черновые; это не утверждённые условия работодателя и не основание менять каталог или офферы. Evidence и пути: `C:/Users/admin/Desktop/Project/outputs/focus-vacancy-pdf-20261020/EVIDENCE.md`. Рабочие данные и production не менялись.


## 2026-10-30 — экран входа и сброс пароля

В /opt/focus-group/static/focus-minimal.css экран входа ограничен колонками 520/440 с промежутком 64px (32px на средней ширине, вертикальный поток mobile). Нормализация почти белого фона перед invert/screen устранила прямоугольник гравюры в тёмной теме. Обновлена версия CSS в index.html; прежние незавершённые изменения сохранены. Server CSS commit cd0e384, пересобран только app, healthy. Браузер 1440/900/390px в обеих темах без overflow, labels связаны. По запросу сброшен пароль подтверждённого ADMIN со скриншота, старые сессии отозваны; реальный вход HTTP200 ADMIN. Секреты вне wiki. Доказательства: C:/Users/admin/Desktop/Project/outputs/focus-login-20261030/EVIDENCE.md, verify.log, browser.log; rollback /opt/focus-group/backups/login-20261030/. Проверено 2026-10-30.


### 2026-10-30 — исправление подвала и sidebar после входа

Публичный footer вне app заставлял sticky sidebar уезжать при прокрутке к низу. Footer продублирован внутрь main, внешняя версия скрыта только в рабочем интерфейсе; main/view заполняют viewport, навигация имеет собственный scroll и компактное выравнивание. Профиль и активная ссылка используют theme tokens, hidden login защищён от mobile display override. Финальный CSS commit 4ff79dd, app healthy, source/container SHA совпадают. Авторизованный экран «Продукты» проверен 1440/900/390 в обеих темах: без overflow, sidebar y0, подвал в колонке main, mobile menu открывается. Evidence C:/Users/admin/Desktop/Project/outputs/focus-login-20261030/shell-browser-final.log и EVIDENCE.md; rollback /opt/focus-group/backups/shell-20261030/.


## 2026-10-30 — стиль рабочего интерфейса TrafficHub

По прямому запросу владельца основной SPA Focus Group переведён на проверенную систему TrafficHub: нейтральные light/dark tokens, локальный Inter, sidebar208/topbar64, заголовки24, панели12px, тонкие границы и компактные формы/таблицы. Новые static/focus-workspace.css и focus-inter.woff2, ссылка последней в index.html; существующий логотип и бизнес-логика сохранены. На телефоне drawer, доступные theme/main action,44px controls,16px inputs, локальная прокрутка досок/таблиц и dialog внутри viewport. Блок следующего шага кандидата изолирован от aside mobile transform. Публичные отдельные onboarding страницы не заменялись.

Финальный server commit0576b4367aa2580d335b61937b878167e3e235de после801c760, app healthy. SHA11backend/JS файлов до/после идентичны. Published108cases:9admin tabs ×1920/1366/1024/768/390/320×2themes без document overflow; поиск/сортировка/карточка/диалог/menu/theme PASS.32synthetic cases8candidate stages; финальные18overview/support и6login cases PASS, реальный Inter loaded. Полный onboarding/sign/payment lifecycle и отдельная аутентификация остальных ролей не заявляются. Данные не менялись. Evidence C:/Users/admin/Desktop/Project/outputs/focus-style-20261030/EVIDENCE.md, live-results.log, candidate-results.log, final-results.log, verify-final.log. Rollback /opt/focus-group/backups/traffichub-style-20261030/index.html + rebuild app. Проверено2026-10-30.
