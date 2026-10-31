# CRM UI локализация

## Актуальные логи и рассылка — проверено 2026-10-16

Финальное уточнение пользователя касалось одинаковой высоты строк логов: **40 px**, одна строка с многоточием; click/Enter/Space раскрывает полный текст, повторное действие сворачивает, используется aria-expanded. Колонка времени 128 px на desktop / 88 px на mobile, сообщение занимает остаток. Равные половины колонок были неудачным промежуточным вариантом и не являются текущим правилом. Commit `c4c1b667e`; Chromium fixtures dark/light 390/1440 подтвердили высоту и клавиатуру, но не заменяют проверку авторизованной страницы.

Расписание рассылки вынесено из скрытого шага к статусу: видны окна времени, текущий момент и последние фактические отметки; несохранённые настройки обозначаются как preview. Выбор Telegram/Android аккаунтов — выпадающий multiselect с существующими checkbox и payload; Escape и click вне закрывают список. Проверены fixtures, полный authenticated live browser не подтверждён. Runtime hashes CSS/JS логов и schedule/dropdown совпали с repo: `C:/Users/admin/Desktop/Project/outputs/baza-reconcile-20261016/runtime-files.txt`.

Историческая запись, ранее пропущенная в wiki: 14 октября admin/device7/APK146, прогрев 180 секунд принят как job28 queued; существующее расписание 09:00–18:00 Europe/Moscow не менялось. Это не доказательство начала или успешного завершения на телефоне и не текущий статус устройства. Доказательство: `C:/Users/admin/Desktop/Project/outputs/admin-warmup-20261014/EVIDENCE.md`.

## Назначение

CRM-интерфейс TrafficHub показывает пользователю русские человекочитаемые подписи, но не изменяет канонические значения, которые приходят из API, партнёрских сетей и БД.

## Подтверждённые факты

- Таблица CRM-лидов загружается из `/traffic-api/leads`.
- Основной рендер находится в `/root/TrafficHub/dashboard/app.js`.
- Статусы переводятся функцией `crmStatusText`.
- Цвет бейджа определяется функцией `crmStatusClass`.
- Текст оффера с техническим типом в квадратных скобках переводится функцией `crmOfferText`.

## Текущее правило отображения

- `rejected` / `declined` показывается как `отклонён`.
- `approved` показывается как `подтверждён`.
- `converted` показывается как `конверсия`.
- `duplicate` / `dup` показывается как `дубль`.
- `[sale]` показывается как `[продажа]`.
- `[lead]`, `[leads]`, `[cpl]` показывается как `[лид]`.

## Почему так

Партнёрские сети и постбеки используют свои технические значения. Если менять их при записи в БД, можно сломать фильтры, аналитику, повторную обработку и расследование источника данных. Поэтому локализация должна быть только презентационным слоем.

## Ограничения

Новые статусы интеграций нужно добавлять явно. Если UI показывает неизвестное английское значение, это не ошибка БД, а отсутствие нового правила отображения.



## 2026-10-04 — меню полного цикла и единая авторизация

По прямому запросу пользователя подготовлена production-реализация согласованного референса: стрелка рядом с «Запустить цикл» раскрывает «Выгрузка» и «Рассылка». Пункты вызывают существующие `runCmd('upload')` и `runCmd('send')`, основная кнопка — `runCmd('run')`. Сохранены ограничения по роли, allowed access и занятости задания; меню закрывается после выбора, с Escape и при уходе фокуса. Проверки команд выполнены только на локальном mock API, реальные рассылки не запускались.

Вход, регистрация и публичные auth-result страницы используют общий `dashboard/auth.css` и `auth-theme.js`. Удалены отдельные старые login CSS, декоративная сетка, цветной autofill и старый inline stylesheet регистрации. Формы, ID, backend-функции авторизации и проверки ключей сохранены. Старые декоративные синие/лаймовые/фиолетовые значения в затронутых CSS и графиках заменены нейтральными токенами текущего интерфейса; семантические статусы сохранены. CSS-селекторы и layout исходных разделов отдельно проверены валидатором.

Проверено 2026-10-04: 72 browser cases (14 вкладок, светлая/тёмная тема, desktop/mobile, auth 320/390/1440, формы, клавиатура, guards), 30 целевых source tests, JS syntax, backend AST equivalence, 353 прежних HTML ID и 30 role/route атрибутов; `git diff --check` PASS. Доказательства: `C:/Users/admin/Desktop/Project/outputs/ui-actions-auth-release-20261004/browser-checks.json`, `static-checks.json`, PNG login/register/overview-menu, server worktree `/home/codex/ui-actions-auth-20261004`. UI commit `a8338488d07f0e6638859d292373ffb1cade7a45`.

Во время release Extended checks выявил ошибку selection policy: explicit pytest paths повторно выбирали retired Account Manager suite, хотя `tests/conftest.py` уже исключает её при отсутствии `AccountManager/api/main.py`. В `tools/test_scope.py` применены те же узкие исключения; тест проверяет absent/present legacy tree, зависимый и явный выбор, сохранение активного smoke и похожего имени. 7 scope tests PASS; commit `687c5ea7507f294adbda457507514ee9cb0c316d`. Исходное падение: GitHub Extended run `37198449450`, `test_account_manager_token_denied_for_user`, отсутствующий ранее удалённый `server.account_manager_token`; сам endpoint не возвращался.


### Production подтверждён — 2026-10-04
Коммит `687c5ea7507f294adbda457507514ee9cb0c316d` развёрнут штатным GitHub deploy `37199166951` (SUCCESS). CI `37198831722`, Extended `37198831708`, Build `37198831758` зелёные. `/root/TrafficHub` HEAD и origin/main совпадают; app/worker и связанные сервисы healthy, app image содержит точный SHA. Maintenance off; `/api/health` внутри `/app` и публично HTTP200 ok. SHA256 шести основных файлов в repo и `/app` совпадают. `/login`, `/register`, auth.css, auth-theme.js и overview-reference.js публично HTTP200.
Live browser: меню действительно раскрывает «Выгрузка»/«Рассылка», Escape возвращает фокус, overflow отсутствует, console errors нет. Публичная регистрация проверена в обеих темах; формы активации и реальные задания на проде не отправлялись. Доказательства: `C:/Users/admin/Desktop/Project/outputs/ui-actions-auth-release-20261004/runtime-proof.txt`, `public-proof.txt`, `production-menu.jpg`, `production-register-light.jpg`, `production-register-dark.jpg`; команды `verify-runtime.sh`, `verify-public.py`. Server outbound TLS probe однажды завершился timeout; публичная проверка выполнена с клиентского компьютера и реальным браузером. Локальный screenshot login соответствует тем же проверенным auth файлам.


### 2026-10-07 — изоляция CRM-лидов для всех ролей

Подтверждён обход tenant фильтра для роли admin в `traffic_hub/api/routers/leads.py`, при этом несколько production аккаунтов имеют эту роль. Task commit `b6cd0c3a11a8ddaa08ef3edfb70550f25901169d` ограничивает list/count/export и карточку/изменение текущим tenant даже для admin; при отсутствующем tenant list/export пусты. JOIN Lead/Offer проверяет совпадение tenant. Данные БД не переназначались. Выпущено app-only в составе `09aeac186feaaa82c8f1e187ee838df819a742a2`, deploy https://github.com/sergkuz219034-boop/TrafficHub/actions/runs/37674864510 success. 12 targeted tests PASS. Реальный HTTP JWT smoke 6 существующих пользователей: admin tenant1 видит2186 конверсий, другие аккаунты не получают его ID в list/CSV. В БД tenant1 отсутствуют Lead rows, поэтому foreign-card404 подтверждён isolated regression, а не live карточкой. Health200, maintenance off; worker не перезапускался. Evidence: `C:/Users/admin/Desktop/Project/outputs/crm-private-leads-20261007/EVIDENCE.md`, `runtime_smoke.py`; `/root/TrafficHub/harness/state/receipts/crm-private-leads-20261007-evidence.json`. Это ограничение относится к API лидов; другие CRM разделы этой задачей не проверены.

## 2026-10-11 — статистика над логами в Обзоре
Проверено по production: в `dashboard/overview-reference.js` блоки идут в DOM в порядке hero → период/фильтры → статус загрузки → метрики → логи/прогресс → офферы. Перенесён существующий `overview-log-panel` под показатели; ID и обработчики сохранены, порядок чтения совпадает с визуальным. Cache-busting JS обновлён в `dashboard/index.html`. Server commit `055e3c5971acd769a131fe4f013e4fdc500c9c7c`, пересобран и пересоздан только `autolead_bot`/`traffichub_app`. JS syntax, diff check и detector PASS; production browser: desktop и 390px, light/dark, метрики выше логов с интервалом 24px, overflow отсутствует. Health внутри контейнера и публичный ok. Evidence: `C:/Users/admin/Desktop/Project/outputs/overview-order-20261011/` (`live-checks.txt`, `result.png`, `overview-reference.js`).

## Рассылка: единый список устройств — 2026-10-13
В шаге «Аккаунты» убран отдельный верхний список `tg-mailing-device-selection`. Выбор для рассылки находится в единственной карточке `tg-mailing-devices` внутри управления устройствами; checkbox доступен активным устройствам, имеет aria-label и описание готовности. Выбор сохраняется при обновлении списка; payload `device_ids` использует новый контейнер. Общий код `dashboard/app.js` и `dashboard/index.html`, server commit `8028aca4c`. Live browser: desktop обе темы, mobile390x844, без overflow/console errors; app health ok. Доказательства: `C:/Users/admin/Desktop/Project/outputs/mailing-device-dedup-20261013/EVIDENCE.md` и screenshots в том же каталоге. Рассылку не запускали.

## Лупа в обзоре: поиск лида — 2026-10-13
Верхняя лупа `overview-reference-global-search` теперь «Найти лида»: открывает Обзор (`switchTab('leads')`), прокручивает к `f-q`, ставит фокус и выделяет прошлый запрос. Использует существующий поиск `/api/leads` по имени/телефону с owner-scoped доступом; фильтры сохраняются. Ранее открывала аналитику/поиск оффера. Server commit `de49c1d99`; node syntax/diff/health PASS; live browser имя6/6, отсутствующий запрос0/0, mobile focus и nooverflow, обе темы, console errors[]. Доказательства `C:/Users/admin/Desktop/Project/outputs/overview-lead-search-20261013/EVIDENCE.md`.

## Android: аккаунт не определён — диагностика 2026-10-13
Read-only device23090RA98G:последнийreport~2дняназад,0.1.139,liveEnabledfalse/operator_stopped,нетaccountPhone/verifiedsenderidentity. PublishedAPK140содержитinspectAfterPairавтооткрытиеtg://settingsonceperbinding. «Открыть выбранный аккаунт»в139/140открываеттекущийTelegramprofile;непереключаетexistingaccountbynumber. BackendbindingномерполучаеттолькоотSenderIdentitySourcetelegram_settings. Текущеефизическоесостояниетелефонанеизмерялось;lastreportнельзяобъявлятьcurrentversion. Evidence `C:/Users/admin/Desktop/Project/outputs/android-account-diagnosis-20261013/EVIDENCE.md`;Androidfilesвoutputs/android-pairing-errors-20261011. Изменений/отправокнебыло.

Уточнение2026-10-13: уDmitryownAndroiddeviceid9/sdk_gphone_x86_64online(healthage1s),140,всеразрешения+liveEnabledTrue;verifiedphone/sourceполяотсутствуют,bindingphoneempty. Adminoffline/139неприменимо. Автоprofileinspection140маркируетattemptприstartActivity,неуспешныйcapture;этоcheckedcodeweakness,конкретныйэкранDmitryнепроверен(LocalADBempty). Evidence outputs/android-account-diagnosis-20261013/EVIDENCE.md дополнено. Usercredentials/номернепубликуются.

## Android141 и числовые поля рассылки — 2026-10-13
PublishedAPK141исправляетодноразовыйprofileattempt:подтверждениепослеactualthSenderPhonecapture,повторonResumeпосле30sпоканеопределённомер;manualprofileallowedarmedidle,активные/pendingзадачинепрерываются. Profile/MyProfile/RUmarkers+shortnotificationssupported,uniquephone+officialpackageguardsсохранены.18identitycases/DEX/signaturePASS;Dmitryещёнужноустановить141,physicalendtoendнеобъявлятьPASS. Source8ee2fd91e,tools/android_ui/LOGIN141.md. Evidenceoutputs/android-account-fix-20261013/EVIDENCE.md.
Числовыеполярассылки:padding12/14,height48,tabularfigures,labelsот/до/limit,desktop3mobile2+limitfullwidth. IDs/60/90/50/minmaxunchanged. ServedoptimizedCSSнужноправитьвместесsourcepicker:прежнийbuilderсоздаётдругойbundleиодногоsourceизменениянедостаточно. Commits5aebeb083/b69c4476e. Evidenceoutputs/mailing-numbers-20261013/EVIDENCE.md/screenshots. Толькоapprestart,workerunchanged.

## Android142: автоматическое открытие профиля — 2026-10-13
ПользовательпотребовалавтоматическоеповедениепоприсланномуKelvinbase.apk(SHA9d64d0d79e9c52ceb0ab6f1f77c4df6721f40772b154fdf5804cc6646160540c). Текущийreferenceпоказываетopen_settings/verify_senderstage;TrafficHub142послеautoinspectionоткрываетtg://settingsиboundedaccessibilitynavigation(30×700ms)черезProfile/Settings/menu,ждётactualSenderIdentitycapture. Officialpackage/flightpendingguardsсохранены,loginOTPнеавтоматизируется,номернеподставляетсябезcapture. CompiledJava/APKsignature/DEXguardsPASS;physicaldeviceDmitryнедоступенLocalADB,послеустановки142нуженfreshhealthдляendtoendproof. Commit381559308. Evidenceoutputs/android-auto-account-20261013/TelegramLogin.java/build142.py/proof.json;servertools/android_ui/rebuild142.py.

## Карточки ИИ-агентов — 2026-10-13
Размерывыравненывнутристрокикаталога,adaptivegridmin280/gap16/padding20/header2lines/avatar44/footerbuttonalign;mobile1column. Commitf3922aa21,servedoptimizedCSS+sourceai-card-sizing.css. Live1440firstrow3cards304×332,390nooverflow;ничегоизagenttogglesнезапускалось. Evidence `C:/Users/admin/Desktop/Project/outputs/ai-card-sizes-20261013/EVIDENCE.md`,desktop-dark.png,mobile-light.png. Второйрядможетиметьдругуювысотупоконтенту;необъявлятьвсеглобальныеheightравными.

## Пул прогрева и проверка отправителя — 2026-10-13
Пользовательуточнил:несколькоаккаунтовнаодномустройстве,сначалапулвкабинете,затемвыбор/подтверждениевTelegram. Commitfa4aa8b8a/APK143:несколькособственныхаккаунтов+Проверитьпул,последовательныеowner-scoped sender_only checks;APKmanualcheckgateподдерживаетsender_only,спонтанныйinspectAfterPairотключён. Толькоactualcaptureverifiedphoneдобавляетподтверждение;saveпроверяетownedaccountIDs+verifiedphones,schedulerчередуетpoolвслотах. Singlephonelegacyfallbackсохранён;schemaнеизменена.28targettestsPASS,public/internalhealthOK. ФизическийE2EDmitryпослеустановки143pending;browserQAtoolblockedbyclient,необъявлятьPASS. Evidence `C:/Users/admin/Desktop/Project/outputs/account-selection-20261013/EVIDENCE.md`,COMPARISON.md.
ТочныйuserKelvinbase.apkSHA9d64d0d79e9c52ceb0ab6f1f77c4df6721f40772b154fdf5804cc6646160540cпоказываетTelegramCheckopen_account_menu/account_selected/verify_sender. Fullparityнеподтверждена:roster/discovery/workprofilesиfolderprobesотличаются. Adminjob23needs_reviewchannels_folder_exists_tab_not_found,нетcompletedпрогрева. Пулобычнойрассылкиэтимизменениемнеобъявляетсяреализованным.

### Пул рассылки и физическая проверка прогрева — 2026-10-13

Добавлен пул проверенных телефонов на выбранных собственных устройствах для обычной Android-рассылки; отдельный accountPhone в каждой задаче, сохранение в owner-scoped schedule JSON без миграции. Дневные резервации и фактическая проверка отправителя сохраняются. Пустые галочки не восстанавливаются при обновлении UI. Серверные коммиты e238fb4b1/9e2ff0017; 31 целевой тест PASS, browser interaction/theme/mobile smoke PASS.

Физическая проверка admin на APK144/Telegram13.0.2: job24 подтвердил аккаунт, но завершился за18сек needs_review/channels_folder_tab_missing без чтения каналов. APK146 fb7e30100 добавляет ограниченный fallback поиска верхней вкладки и семантические Back/scroll с конечными лимитами; 8 JVM fixtures PASS, прежняя подпись. Работа146 на телефоне пока не подтверждена. Полная эквивалентность Kelvin, client_roster и work profiles пока не реализованы.

Доказательства: C:/Users/admin/Desktop/Project/outputs/kelvin-pool-20261013/{EVIDENCE.md,tests-final.txt,warmup-status.txt,pool-mobile-light.png,proof146.json}; точный референс ../account-selection-20261013/kelvin-reference.

## Выбор аккаунтов прогрева и рассылки — 2026-10-14

Текущий выпуск `322c32cd8214df64986467a0bf6195d99ab81c17`: пользователь выбирает owner-scoped аккаунты из «Мессенджеров» галочками и запускает программу/рассылку. Ручные кнопки проверки предыдущего выпуска a1b2c080c удалены по уточнению пользователя; выключать и включать выполнение для проверки аккаунтов больше не нужно. Предварительное подтверждение телефона на устройстве не требуется: собственные ID/номера проверяются по telegram_accounts, выбранный target accountPhone передаётся Android. APK146 уже выполняет account selection/verification; перед отправкой authorize_job и sender_readiness по-прежнему проверяют фактическую identity и соответствие job. Счётчики, резервации, неопределённые результаты и APK не менялись. Нужны подключённое разблокированное устройство и разрешённое выполнение.

Новый выбор пустой, review показывает весь пул, обновление не восстанавливает снятые галочки. Manual warmup использует первый сохранённый account_pool; scheduler чередует пул. 43 scoped tests PASS, 4browserfixtures(light/dark,390/1440)PASS; apphealthy,6runtimehashesmatch,workerunchanged,publichealthok. Единственный исключённый test_warmup_planner.py::test_scheduled_slot_and_fact_and_no_duplicate ранее воспроизведён на baseline (planned вместо leased); этим выпуском не исправлялся. Physical multi-account switching на телефоне пользователя при QA не запускался.

Доказательства: C:/Users/admin/Desktop/Project/outputs/automatic-account-launch-20261014/{EVIDENCE.md,tests.txt,browser.json,result.txt}; предыдущий baseline failure: outputs/account-choice-20261014/baseline-failure.txt.

## 2026-10-14 — автоматическое обновление разделов

По запросу пользователя удалены ручные кнопки обновления из разделов dashboard, CRM, источников, вакансий, аналитики, диагностики, админки, рассылки и интеграций; вместе с ними убраны ручные проверки списка устройств, результатов Zvonok и статусов SMS. Maintenance overlay уже опрашивал режим каждые 15 секунд, поэтому его кнопка перезагрузки также удалена. В диагностике оставлена скрытая и отключённая команда «Обновить и перезапустить» runtime: это действие выпуска, а не обновление данных.

`dashboard/live-data.js` обновляет открытую вкладку и останавливается при скрытой странице, потере сети, открытом редакторе или фокусе ввода. Интервалы: большинство вкладок 5 секунд, источники/вакансии/ИИ/рассылка/диагностика 15 секунд, HH/admin/CRM-сети/финансы/настройки 30 секунд; при ошибках интервал растёт до 30 секунд. Для SMS список обновляется в фоне, а отправленные/частичные/неопределённые кампании синхронизируются не чаще раза в 30 секунд. Zvonok обновляет кампании каждые 15 секунд и синхронизирует текущий статус, не перезапуская отправку. В мастере прогрева обновляется список устройств с сохранением выбора аккаунтов.

Проверено 2026-10-14: 6 JS-файлов проходят `node --check`; `git diff --check` PASS; в браузере открыты 14 основных вкладок — видимых ручных кнопок обновления нет, ошибок console нет. При ширине 342 px горизонтальной прокрутки нет; тёмная и светлая темы проверены, исходная тема восстановлена. Production health `ok`, app hashes совпадают с commit `12fcaad71819db40e714014bb632c43ab6ea2f69`, worker не перезапускался. Evidence: `C:/Users/admin/Desktop/Project/outputs/auto-refresh-ui-20261014/EVIDENCE.md`.

## Сводка расписания в проверке рассылки — 2026-10-15

В карточке «Новая рассылка» рядом с предпросмотром показаны сохранённые дни, окно с timezone и переходом через полночь, состояние ожидания окна, Android/Telethon, случайный интервал и суточный лимит. Для начатой кампании параметры берутся из API, для черновика — из формы. Сохранение расписания не запускает отправку; вне окна новые отправки ожидают. Server commit `1971c5954`; последующий runtime 2026-10-15 сохранил оба JS byte-identical. Chromium fixture dark/light 390/1440 PASS; полный live browser заблокирован ERR_BLOCKED_BY_CLIENT, public health ok. Отправку не запускали. Доказательства: `C:/Users/admin/Desktop/Project/outputs/mailing-summary-20261014/EVIDENCE.md`, `browser.json`, `verified-runtime.txt`.

## Наглядное расписание и выпадающий выбор аккаунтов — 2026-10-15

Исправление предыдущей реализации: текстовая сводка не заменяет видимый план/факт. `mailing-today` вынесен из скрытого шага в самостоятельный блок перед статусом, виден и на «Проверке». Сохраняет шкалу/список, текущее время, рабочие окна и отметки отправок из последних 30 записей; при отключённом расписании окно круглосуточное. На проверке отображается сохранённое расписание, при редактировании несохранённые изменения помечены. Commit `e74d11ecb`.

По последующему запросу Telegram-аккаунты и Android pool выбираются через выпадающий multi-select (native details), исходные checkbox и payload selectors сохранены. Имя/счётчик выбранных, Escape и закрытие снаружи; observer поддерживает динамическую загрузку. Commit `b4f8def5c`. Проверки обоих изменений: Chromium fixture, обе темы, 390/1440, целевые interaction checks; app-only deploy. Доказательства: `C:/Users/admin/Desktop/Project/outputs/mailing-visual-schedule-20261015/EVIDENCE.md`, `C:/Users/admin/Desktop/Project/outputs/mailing-account-dropdown-20261015/EVIDENCE.md`. Полный authenticated live browser не проверен; отправки не запускались.

## Равные колонки журнала — 2026-10-15

По запросу пользователя desktop/mobile журнал overview-log-panel получает две равные содержательные колонки «Время»/«Сообщение», между ними отдельный18px status marker. Единая grid/отступы для обычных и realtime spinner строк; длинные сообщения/неразрывные слова переносятся без обрезки; область журнала320–560px с внутренней вертикальной прокруткой. Keyboard focus region сохранён. Изменения ограничены dashboard/log-columns.css и подключением/заголовком в index.html. Commit be584de96. Chromium fixture с dashboard CSS dark/light390/1440: равенство ширин, идентичная позиция сообщений, long-text overflow, realtime rows, focus PASS; полный live authenticated browser не проверен. Evidence C:/Users/admin/Desktop/Project/outputs/log-columns-20261015/browser.json, browser.py, screenshots, deploy.txt. App-only overlay от актуального apk150; rollback узкий revert и rebuild от текущего runtime. Логирование/очистка/скачивание/автопрокрутка JS не менялись.

### Исправление по скриншоту пользователя — 2026-10-15
Равные половины для времени/сообщения оказались неверной интерпретацией: пустая половина снижала читаемость. Новая геометрия фиксирует одинаковую ширину времени во всех строках128pxdesktop/88pxmobile, marker18px, сообщение занимает остаток. Заголовок сообщения скорректирован по исходной header/body grid geometry. CSS cache-busting обновлён. Commit ec352204f. Chromium dark/light390/1440 PASS: стабильные time widths/позиции, message wider, overflow и focus; скриншоты обновлены в outputs/log-columns-20261015. Evidence outputs/log-readable-20261015/deploy.txt; app-only overlay от актуального apk150-logs. Старое требование равных половин отменено исправлением по screenshot; основной критерий — выравнивание и читаемость.

### Уточнение пользователя: одинаковая высота строк — 2026-10-15

Пользователь явно подтвердил, что «колонки» означали высоту строк. Все закрытые записи и spinner теперь40px, сообщение однострочное с ellipsis. Click/Enter/Space раскрывают полный текст (aria-expanded), повтор сворачивает; динамические строки декорируются observer без пересоздания. Временная колонка128/88 сохранена. Commit c4c1b667e; node --check/diff PASS; Chromium dark/light390/1440: measured40px, expanded>40, collapse40, keyboard/focus/no overflow PASS. Evidence C:/Users/admin/Desktop/Project/outputs/log-columns-20261015/browser-rows.py, browser.json, screenshots; release в outputs/log-row-height-20261015/deploy.txt. App-only overlay, worker/data не менялись; rollback узкий revert + current-base app overlay. Проверка fixture, не authenticated live browser.
