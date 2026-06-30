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
