# 2026-07-01 Admin forms not filling complaint

## Симптом

Пользователь сообщил: "не заполняются анкеты". На скрине партнёрской аналитики за `01.07.2026` видно `Клики: 60`, `Конверсии: 3`.

## Зона системы

- `modules/vbiv_bot.py`
- `modules/platforms/lovko.py`
- PostgreSQL:
  - `autolead_send_history`
  - `autolead_retry_queue`
  - `autolead_job_events`
  - `autolead_run_log`
  - `postback_logs`
  - `conversions`

## Гипотеза

Первичная гипотеза про остановленный job была неполной. Скрин партнёрки показывает дневные конверсии, где `конверсия = успешное заполнение анкеты`. Значит локальный `autolead_send_history.status='sent'` нельзя считать доказательством заполнения, если партнёрка не видит соответствующую конверсию.

Рабочая гипотеза после уточнения пользователя: Lovko/Ozon/Onecta success detection всё ещё был слишком мягким и мог записывать `sent` по UI-признакам, которые не доказывают принятие анкеты партнёркой.

## Проверка

- Live HEAD до нового фикса: `c247fed81`.
- За `2026-07-01` в `autolead_send_history` по `admin` после свежего строгого фикса:
  - `Onecta #2`: `5` строк `sent`, `21:06:48` - `21:11:39`;
  - `Ozon`: `4` строки `sent`, `21:07:14` - `21:10:38`.
- В `autolead_job_events` для job `8c98a427546840bfb60a55461628552b`:
  - `job_start`: `21:00:09`;
  - `job_stop_requested`: `21:11:54`;
  - `job_stop`: `21:11:57`;
  - progress на stop: `forms_done=9`, `forms_total=10`, `total=9426`.
- В `autolead_retry_queue` у `admin` есть только `Самокат`:
  - `8` строк;
  - error: `samokat: landing пустой или форма не найдена`;
  - retry_count `1..3`.
- За `2026-07-01` в `conversions` нет строк по admin.
- В `postback_logs` по admin за день есть Voxys `pending/rejected` с `payout=0`, но нет оплаченных конверсий.
- Runtime proxy check из `traffichub_app` под owner `admin`:
  - `_playwright_proxy_from_config()` возвращает `http://217.29.62.68:8000`;
  - HTTP и Playwright egress через proxy показывают IP `217.29.62.68`, geo `RU/Moscow`.
- Code check `modules/platforms/lovko.py` на `c247fed81`:
  - `_wait_lovko_success()` уже не принимал обычный redirect за success;
  - но всё ещё принимал body/content/modals с общими success words и даже видимую `[data-fancybox-close]` как `ok`;
  - это могло давать ложный `sent`, если сайт показал popup-shell/общий текст, но партнёрка не зарегистрировала заявку.

## Наблюдение

Факт runtime не подтверждает старый вывод "9 форм точно заполнены". Он подтверждает только, что бот записал `9` локальных `sent`. После уточнения пользователя и сверки со скрином ПП это недостаточно: партнёрская конверсия является внешним подтверждением принятой анкеты.

Отдельная подтверждённая проблема — `Самокат` не доходит до формы и остаётся в retry. Но текущий фикс касается только ложного success для стандартных Lovko/Ozon/Onecta.

Скрин партнёрки показывает клики/конверсии ПП, а не напрямую `autolead_send_history`. После commit `39e72fa2b` редирект больше не считается успехом без явного подтверждения формы. После commit `190abe7b3` Lovko/Ozon/Onecta также не считают success по общему body/content и пустым popup-shell.

## Вывод

Причина повторного расхождения `успешно заполнен` vs конверсии ПП — недостаточно строгий Lovko success detection: локальный `sent` мог появляться без доказанного принятия анкеты партнёркой.

Исправление:

- Product commit: `190abe7b3 fix: require explicit lovko form confirmation`.
- `modules/platforms/lovko.py::_wait_lovko_success()`:
  - больше не принимает body/content с общими success words как `ok`;
  - больше не принимает один видимый `[data-fancybox-close]` как `ok`;
  - принимает success только по явному `.thanks-modal`/dialog с новым success text или alert/dialog success;
  - duplicate по явному modal/dialog сохраняется.
- Добавлен тест `tests/test_lovko_success_detection.py`.

Проверка:

- `python3 -m pytest -q tests/test_lovko_success_detection.py tests/test_platform_success_detection.py tests/test_proxy_config.py`: `15 passed`.
- `python3 -m pytest -q`: `439 passed, 43 skipped`.
- GitHub checks для `190abe7b3`: `CI` success, `Build and Push Docker Image` success.
- Live deploy: `docker compose up -d --build autolead_bot worker`.
- Runtime: `traffichub_app` и `traffichub_worker` healthy; `/api/health` ok.

## Следующий шаг

1. Дать полному циклу доработать без stop уже после `190abe7b3`, затем сравнить:
   - `autolead_send_history`;
   - `postback_logs`;
   - `conversions`;
   - партнёрскую аналитику.
2. Если `Самокат` нужен в активной рассылке, открыть отдельный incident по `samokat: landing пустой или форма не найдена` со свежим debug HTML/screenshot.
3. Не возвращать слабое правило `redirect = success`: оно уже давало ложные "успешно заполнен" без конверсий.

## Дополнение 2026-07-01: smoke-test admin offers

Симптом: пользователь попросил взять admin offer links и вручную прогнать каждый активный оффер на одном лиде.

Проверка:

- Active admin offers:
  - `Onecta #2`: `https://tracking.lovko.pro/L6eTlM`;
  - `Я еда`: `https://tracking.lovko.pro/fik03d`;
  - `Ozon`: `https://tracking.lovko.pro/3xaBLJ`;
  - `Самокат`: `http://work.jobs-samokat.ru/click?pid=4161&offer_id=133&sub1=1`.
- Runtime proxy для browser form-fill: `http://217.29.62.68:8000`; `api.ipify.org` внутри Playwright показывал `217.29.62.68`.
- Найдено: Lovko tracking preflight в `modules/vbiv_bot.py` мог идти через server-side `requests` до запуска Chromium. При включённом proxy это обходило browser proxy для click/tracking.
- Исправлено:
  - `55745fbb1 fix: route lovko tracking through form proxy` — при `form_proxy` tracking URL открывается Chromium через proxy.
  - `d596c7f5e fix: fill lovko residence address fields` и `54af44d1b fix: wait for lovko residence city suggestions` — `place_of_residence` выбирает Dadata city suggestion, а не пишет произвольное значение.
  - `ad26ccbb4 fix: choose ozon moscow region city fallback` — Ozon для Москвы использует fallback query `МО`, потому что dropdown отдаёт склады `МО, Домодедово`, `МО, Жуковский`, `МО, Подольск`, а не `Москва`.

Наблюдение после deploy:

- `Onecta #2`: smoke ok, proxy IP `217.29.62.68`.
- `Я еда`: smoke ok, proxy IP `217.29.62.68`.
- `Ozon`: smoke ok после Ozon fallback `МО`, proxy IP `217.29.62.68`.
- `Самокат`: не form-fill bug в текущем коде; target уводит на `disabled.html`, результат `samokat: landing пустой или форма не найдена`.

Вывод:

- Основной proxy/IP баг был не в Chromium proxy, а в server-side Lovko tracking preflight.
- Основной form-fill баг для Onecta/Ozon был в city/dropdown validation.
- `Самокат` требует отдельного решения по офферу/ссылке: текущая ссылка отключена на стороне landing.
