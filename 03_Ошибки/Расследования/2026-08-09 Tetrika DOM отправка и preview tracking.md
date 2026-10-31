# Tetrika DOM отправка и preview tracking

## Симптом

TrafficHub сообщал об успешном заполнении Tetrika, но конверсия не появлялась в Lead.su.

## Зона системы

Offer `11685`, Lead.su redirect, Tetrika landing `sales_manager`, DOM form `form1789963811`.

## Гипотеза

Форма advertiser принимает данные, но сохранённая offer URL работает в preview-режиме и не создаёт партнёрскую атрибуцию.

## Проверка

- Admin offer `868`: `https://pxl.leads.su/aff_c?offer_id=11685&mode=view&erid=get_it_soon`.
- Redirect: `https://tetrika-school.ru/sales_manager/`.
- Redirect parameters: `click_id={preview_mode:transaction_id-}`, `utm_campaign={preview_mode:affiliate_id}`.
- Через видимый Chrome DOM заполнен новый admin-кандидат с email и Rabota resume URL.
- Поля: `job_position`, `last_name`, `name`, `surname`, phone, email, resume, birth date, sales experience `6`, city, citizenship, consent.

## Наблюдение

Advertiser endpoint `POST https://tetrika-school.ru/marketing/api/v1/lead/mass_hiring` ответил `200`. UI показал: «Спасибо! Ваша заявка принята! Мы свяжемся с вами в ближайшее время». Screenshot: `C:\Users\Арт\Desktop\Project\tmp\tetrika-form-success.png`.

При этом `click_id` остался preview placeholder. Значит приём Tetrika подтверждён, attribution Lead.su не подтверждена.

## Вывод

DOM-схема формы рабочая. Первопричина отсутствия конверсии в партнёрке — preview tracking URL. Такой запуск нельзя маркировать `Отправлено`; корректный статус — `Ошибка: invalid_tracking_link` или `tracking_not_confirmed`.

## Следующий шаг

В настройках Lead.su получить реальную affiliate URL для offer `11685`, заменить admin/artem target URL, проверить непустой click ID и выполнить три контрольные отправки по [[Каноническое правило заполнения анкет и офферов]].


## 2026-10-07 — текущая форма «Менеджер по продажам на вводном уроке»
Проверены текущие исходники и реальная анкета через RU worker, по актуальной ссылке admin. В DOM значения job_position совпадают с русскими названиями всех трёх должностей; IntroSales отсутствует. modules/platforms/tetrika.py выбирает точное «Менеджер по продажам на вводном уроке», исправление селектора не требуется.
Реальный TetrikaPlatform.fill заполнил синтетические ФИО, маску телефона, email, резюме, дату рождения, опыт, город, гражданство и согласие и дошёл до защищённой отправки. submit заблокирован до клика; отдельный guard запрещал POST mass_hiring. Приём партнёром и конверсия этим не подтверждены; успешной исторической INTRO отправки в autolead_send_history нет. У admin все три оффера включены, у Alex офферов Тетрики нет. Основной app-контур landing не открывает; фактический RU worker открывает, поэтому это не доказательство ошибки обработчика.
Доказательства: C:/Users/admin/Desktop/Project/outputs/tetrika-three-offers-20261006/INTRO-LIVE-20261007.md; ru_dom_probe.py, ru_fill_probe.py и tetrika-intro-actual-ru-dom.png в том же каталоге. Production при проверке aaab6c5bda251e5e2793a32770ed91514be37d35, RU image traffichub-ru-autolead:high-fixes-20261007.

## 2026-10-09 — submitted form not ready: ошибочный маршрут браузера admin

По точной owner tracking URL admin intro_sales: Chromium основного worker получил chrome-error://chromewebdata/, пустые DOM/form/body и ready=false. На RU traffichub_offer_worker та же ссылка перенаправилась на tetrika-school.ru/sales_manager/, exact-action форма видима, 19 controls, wait_tetrika_form_submit ready=true. POST mass_hiring в probes блокировался; новой заявки не создавалось. Сохранённый form proxy отдельным read-only probe дал TimeoutError, поэтому proxy не включён.

Подтверждено в runtime: REMOTE_AUTOLEAD_ENABLED=false, owners=admin, enabled_for(admin)=False; signed queue configured=True, RU worker running. Исправление конфига: .env REMOTE_AUTOLEAD_ENABLED=true, owners admin сохранён. Server receipt commit 94b3d41de; применение к worker ждёт zero active jobs, script /home/codex/progress-upload-20261009/deploy-when-idle.sh. Нельзя утверждать, что текущий цикл уже использует RU: до recreate он продолжает со старой средой. Evidence C:/Users/admin/Desktop/Project/outputs/progress-upload-20261009/tetrika-probe.log, tetrika-ru-direct.log, tetrika-proxy-probe.log, tetrika-route-fix.log. Ошибка возникает до POST, повторы не требуют выдуманной отметки sent; tracking URL и history не менялись.


## 2026-10-09 runtime verification
Cycles stopped by user instruction; app/worker dcb52f0b696bbed33617c64775f6384990d36e9b healthy, /api/health OK. Admin RU route applied. 85 targeted preset/handler tests passed. Read-only RU probes found forms for VOXYS, Tetrika (all three role options), Samokat, Yandex Food, Dixy, Ozon, X5 walking and bicycle. Onecta destination remains VOXYS; Onecta #2 and Four Paws Disabled; Vkusvill Lovko 43/149 requires_access. No new applicant POST. Historical thank-you screenshots dated 2026-10-07 are separated from current form checks. Fresh submissions await control candidate details. Evidence: C:/Users/admin/Desktop/Project/outputs/presets-final-20261009/REPORT.md, catalog.json, form-0..11.json/png, tests.log, runtime.log.

## 2026-10-10 — Зависшее ожидание RU и неверные 100%
Runtime подтвердил: текущий цикл использует RU, успешные POST mass_hiring отвечают 200. На скриншоте старые ошибки submitted form not ready за 09.10. Новая остановка связана с потерей lease RU task во время недоступности app; wait_result ждал до четырёх часов и не вызывал requeue_expired сам. Штатный requeue_expired завершил одну истёкшую offer_autofill task как uncertain без повторной отправки; parent admin перешёл в error в 22:26:30 МСК. Счётчик RU суммирует forms_done по пачкам, но forms_total относится только к текущей пачке: 33/10 ошибочно ограничивались до 10/10. UI должен показывать общий processed/total для executor=ru: 88/107=82%. Изолированные проверки expiry/no replay и fast polling: 3 PASS. Доказательства C:/Users/admin/Desktop/Project/outputs/tetrika-cycle-20261010/ (логи с персональными данными не переносить в wiki). Server commit 46b68424d626c3dc9845994ee8e5fc4a6feaf191; публикация проверяется отдельно.


Публикация 10.10: app запущен на 46b68424d626c3dc9845994ee8e5fc4a6feaf191, healthy, публичный /api/health HTTP 200. Patch image собран поверх проверенного 5a8401ab7 без смены зависимостей (Dockerfile.patch сохранён на сервере /home/codex/tetrika-cycle-20261010/). Live browser admin подтвердил отсутствие зависшего прогресс-бара и console errors; история ошибок сохранена. Worker всё ещё предыдущий image из-за активного alex job; подготовлен автоматический recreate только worker после zero active owners: /home/codex/tetrika-cycle-20261010/update-worker-idle.sh, PID 3192869. Это отложенная публикация wait_result, не утверждать её завершённой до проверки image. Rollback app: прежний 5a8401ab7 image и env.before в указанной папке; production данные не удалялись, uncertainty не переигрывалась.

