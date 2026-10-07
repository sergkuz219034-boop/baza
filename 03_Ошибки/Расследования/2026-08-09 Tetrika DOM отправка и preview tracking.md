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
