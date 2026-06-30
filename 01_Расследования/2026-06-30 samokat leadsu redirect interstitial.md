# 2026-06-30 samokat leadsu redirect interstitial

## Симптом

- У `alex` в свежих логах повторялась ошибка `Ошибка Самокат [...]: samokat: кнопка submit не найдена`.
- Ошибка признавалась permanent `form-failure`, поэтому retry queue пропускалась.

## Зона системы

- `control_user_app_configs.config_json.offer_mapping`
- `modules/platforms/lovko.py::SamokatLeadsuPlatform`
- `modules/vbiv_bot.py::_is_permanent_form_failure`
- Debug artifacts `data/debug/debug_Самокат_20260630_*.html/png`

## Гипотеза

- У `alex` активен устаревший Leads.su Samokat URL, который больше не доходит до формы `jobs-samokat.ru`.
- Код ошибочно классифицирует промежуточную tracking/LFID страницу без формы как постоянную ошибку submit-кнопки.

## Проверка

- В live config найден один активный Samokat offer:
  - owner `alex`;
  - platform `leadsu`;
  - `enabled=true`;
  - URL `https://pxl.leads.su/click/024264b8acaef0517d7f2442635f70f3?erid=...`.
- Последний debug HTML `data/debug/debug_Самокат_20260630_072143.html`:
  - `forms=0`;
  - `buttons=0`;
  - содержит `lfid.min.js`, `lfid_processed`, `redirectOnce`, `clientctx.su`.
- `curl -kIL` по offer URL показал redirect на `https://logystpartner.ru/...`, после чего запрос таймаутился.

## Наблюдение

- Это не сломанный selector формы: формы на странице вообще нет.
- Root cause: Samokat landing находится в tracking/interstitial state или уводит на недоступный partner host.
- Исправление:
  - `modules/platforms/lovko.py::_is_tracking_interstitial_without_form()` определяет LFID/redirect interstitial без формы;
  - `SamokatLeadsuPlatform` возвращает `samokat: landing пустой или redirect не дошёл до формы`;
  - `modules/vbiv_bot.py::_is_permanent_form_failure()` уже считает `landing пустой` transient, поэтому retry queue больше не пропускается как permanent form-failure.
- Тесты:
  - targeted: `13 passed`;
  - full: `399 passed, 43 skipped`.
- Product commit: `c47e0ac96 fix: treat samokat tracking interstitial as transient`.
- GitHub checks: `CI=success`, `Build and Push Docker Image=success`.
- Live deploy: `autolead_bot` и `worker` пересозданы, оба `healthy`, `/api/health` возвращает `ok`.

## Вывод

- Ошибка `Самокат: кнопка submit не найдена` была следствием устаревшего/нестабильного партнёрского redirect, а не формы.
- Теперь такие случаи не считаются permanent form-failure и не выкидываются мимо retry.
- Сам offer у `alex` всё ещё требует бизнес-решения: заменить URL на актуальный или выключить offer toggle, если партнёрская ссылка больше не работает.

## Следующий шаг

- При следующем прогоне `alex` проверить, что Samokat пишет transient/retry, а не permanent `кнопка submit не найдена`.
- Если Samokat больше не нужен, выключить offer в UI, чтобы не тратить время цикла на недоступную партнёрку.

## Новая анкета Самокат 2026-06-30

Пользователь передал актуальный HTML формы `work.jobs-samokat.ru` / Leadssu.

Подтверждённая структура новой анкеты:

- `form[action="/?utm_source=leadssu..."]`, без `#vacancy_form`;
- скрытые поля `sessid`, `PARAMS_HASH`, `user_post=Курьер`;
- ФИО: `input[name="user_name"]`;
- город: `input[name="user_city"]` + кастомный список `.form-list-item`;
- телефон: `input[name="user_phone"]`;
- пол: `input[name="user_gender"]` + `.form-list-item` (`Мужской`, `Женский`);
- возраст: `input[name="user_age"]`;
- транспорт: `input[name="user_courier_type"]` + `.form-list-item` (`Пеший`, `Вело`, `Мото`);
- state: `input[name="user_state"]`;
- submit — скрытый `input[type="submit"]`, кнопка `button#send_form` отсутствует.

Причина нового сбоя отличается от предыдущего LFID/interstitial случая: redirect уже может доходить до формы, но generic `modules/platforms/leadsu.py` искал старые поля `#lname/#fname/#phone`, `#vacancy_form` и `#send_form`.

Live-исправление в `/root/TrafficHub/modules/platforms/leadsu.py`:

- добавлен fallback на единое поле ФИО `user_name`;
- город, пол и тип транспорта выбираются через `.form-list-item`;
- телефон поддерживает `user_phone`;
- возраст поддерживает `user_age`;
- `user_state` заполняется городом;
- direct submit теперь берёт `form[action]`, а не только `#vacancy_form/send2.php`;
- submit finder видит скрытый `form input[type="submit"]`.

Проверка:

- `python -m py_compile /app/modules/platforms/leadsu.py` в контейнере прошёл;
- Playwright DOM-test на переданном HTML подтвердил `FormData`:
  - `user_name=Иванов Иван`;
  - `user_city=Москва`;
  - `user_phone=+7 (999) 111-22-33`;
  - `user_gender=Мужской`;
  - `user_age=25`;
  - `user_courier_type=Пеший`;
  - `user_state=Москва`;
  - `hasForm=true`, `hasSubmit=true`.
- `traffichub_app` перезапущен, `/api/health` вернул `status=ok`.

Следующий runtime-шаг: на ближайшем заполнении Самоката проверить уже партнёрский submit/response. Текущая проверка доказывает заполнение новой DOM-структуры, но не отправляла боевую заявку.

## Повторный сбой 2026-06-30: скрытая кнопка submit в SamokatLeadsuPlatform

Пользовательский лог `autolead (10).log` подтвердил повторяемую ошибку:

- `Ошибка Самокат [...]: samokat: кнопка submit не найдена`;
- retry queue пропускалась, потому что ошибка считалась permanent form-failure.

Причина: предыдущее исправление было сделано в generic `modules/platforms/leadsu.py`, но фактический routing для `jobs-samokat.ru` выбирает `modules/platforms/lovko.py::SamokatLeadsuPlatform`.

Подтверждённая runtime-структура из нового HTML:

- форма есть: `form[action="/?utm_source=leadssu..."]`;
- submit-кнопка есть: `button[type="submit"][name="submitButton"].btn_form`;
- контейнер кнопки скрыт через `style="display: none"`;
- `_first_visible(page, "button.btn_form", ...)` не возвращал кнопку, потому что она невидимая.

Root cause: для новой анкеты Самоката наличие невидимой submit-кнопки не означает отсутствие формы. Нужно отправлять саму форму через JS, если видимого submit-клика нет.

Фикс product commit `0b2518036`:

- добавлен helper `modules/platforms/lovko.py::_submit_samokat_jobs_form()`;
- если видимой кнопки нет, но `form` существует, используется JS fallback:
  - `button.btn_form` / `button[type=submit]` / `input[type=submit]`;
  - `form.requestSubmit(btn)` если доступен;
  - fallback `form.submit()`;
- tracking/interstitial без формы по-прежнему возвращает `landing пустой или redirect не дошёл до формы`, а не permanent submit failure;
- regression test `tests/test_platform_routing.py::test_samokat_hidden_submit_button_uses_form_submit_fallback` закрепляет скрытую кнопку.

Проверка:

- `python -m pytest -q tests/test_platform_routing.py tests/test_vbiv_bot_navigation.py` -> `14 passed`;
- `traffichub_app` перезапущен;
- `/api/health` вернул `status=ok`.

Вывод: анкета была адаптирована не до конца, потому что был исправлен generic Leads.su path, а live Самокат использует отдельный `SamokatLeadsuPlatform`. Канон: для `jobs-samokat.ru` править и тестировать именно `modules/platforms/lovko.py`.
