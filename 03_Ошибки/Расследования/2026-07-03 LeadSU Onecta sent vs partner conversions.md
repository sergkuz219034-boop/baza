# 2026-07-03 LeadSU Onecta sent vs partner conversions

## Симптом

TrafficHub Autolead показывал `Офферы сегодня`: `Онекта`, `Воксис`, `Ozon`, при этом в партнёрке Lead.su пользователь не видел конверсий Onecta. Скрин TrafficHub показывал `Онекта=381`, `Воксис=277`, `Ozon=172`; позже live `send_history` уже показывал `Воксис=375` из-за продолжающейся работы runtime.

## Зона системы

- Live repo: `/root/TrafficHub`.
- Dashboard metric: `utils/runtime_repository.py::get_owned_summary`.
- Autolead delivery history: PostgreSQL `autolead_send_history`.
- Partner conversions: PostgreSQL `conversions`, `postback_logs`, Lead.su API через MCP/API.
- Lead.su sync: `traffic_hub/api/routers/integrations.py`.
- Lead.su form fill: `modules/platforms/leadsu.py`.

## Гипотеза

TrafficHub показывает не подтверждённые партнёркой конверсии, а внутренние `sent` после заполнения формы. Дополнительно Lead.su form-success detection мог давать ложные `sent` по popup-shell без явного подтверждения партнёрки.

## Проверка

- MCP `lead.su`: токен настроен, API доступен; запрос конверсий за `2026-07-03` возвращал `count=314`.
- MCP `Lovko`: логин/пароль настроены, health `200`, но текущий MCP-набор не даёт прямой метод выгрузки конверсий.
- Live SQL:
  - `autolead_send_history` для `admin` за `2026-07-03`: `Онекта=381`, `Воксис=277`, `Ozon=172` на первом снимке.
  - `conversions` за `2026-07-03`: только `artem / leadsu / Voxys HR [sale] / pending = 287`.
  - За всё время `admin / leadsu` имел только `Voxys HR [sale]`: `28 rejected`, `1 pending`; `admin / Onecta HR [sale]` отсутствовал.
- Admin offer mapping:
  - `Онекта`: `platform=leadsu`, enabled, `target_url=https://pxl.leads.su/...`.
  - `Onecta #2`: `platform=lovko`, disabled.
  - `Ozon`: `platform=lovko`, enabled.
- Manual smoke `2026-07-03`:
  - Через live `run_sender()` отправлен один тестовый лид `admin / Онекта` с телефоном `9001607332`.
  - TrafficHub до дополнительного фикса записал `autolead_send_history.status='sent'`, `fill_time_ms=42115`.
  - Lead.su API по connected offer `Onecta HR [sale]`, `offer_id=10963`, после повторной проверки не показал свежую conversion; по этому offer_id были только старые rejected-записи `2026-06-29` и `2026-07-02`.
  - Тестовая запись удалена из `autolead_send_history`, чтобы не искажать dashboard.
- Code facts:
  - `get_owned_summary()` считал `processed_today` и `offers_today` из `autolead_send_history WHERE status='sent'`.
  - `/traffic-api/settings/integrations/leadsu/sync` вызывал `_sync_network(... username=...)` без `tenant_id`, в отличие от Lovko sync.
  - `LeadsuPlatform` передавал в `_wait_success()` слабые popup-shell селекторы `.fancybox-content`, `.fancybox-slide--current`, `[data-fancybox-close]`, которые общий `_wait_success()` принимал как `ok` без проверки текста.
  - `modules/platforms/__init__.py` дополнительно маршрутизировал `platform=leadsu` + `Онекта` в `TildaPlatform`; этот путь принимал Tilda success-popup как `FillResult.ok()` и создавал ложный `sent`.

## Наблюдение

TrafficHub UI корректно показывал внутреннюю метрику отправок, но эта метрика не равна партнёрской конверсии. Для `admin/Онекта` подтверждён разрыв: сотни `sent` в Autolead и ноль Lead.su conversions в TrafficHub DB/API-sync.

## Вывод

Root cause состоит из двух частей:

- метрика `Офферы сегодня` в Autolead является internal send-history, а не partner-confirmed conversions;
- Lead.su generic form path мог создавать ложные `sent`, потому что popup-shell считался успехом без явного success text или partner response.
- Onecta была отдельным false-positive path: из-за спец-роутинга в `TildaPlatform` она обходила более строгую Lead.su-проверку и засчитывала popup как заполнение.

## Исправление

- Product commit `ff0098114`: `sync_leadsu` теперь передаёт `tenant_id=tenant_id_for(current_user)` в `_sync_network`; добавлен тест `test_sync_leadsu_endpoint_passes_current_tenant`.
- Product commit `87eb74095`: generic Lead.su больше не принимает popup-shell selector как доказательство успеха; если явного success нет, код доходит до direct-submit recovery и проверяет ответ партнёрской формы. Добавлен тест `test_leadsu_does_not_treat_popup_shell_as_success`.
- Product commit `185206758`: удалён спец-роутинг `leadsu + Онекта -> TildaPlatform`; Onecta теперь идёт через `LeadsuPlatform` и не попадает в `sent`, если партнёрская форма не подтверждена.
- Product decision `2026-07-04`: пункт про обязательное подтверждение партнёркой из `185206758` устарел. Для Lovko и LeadSU канон теперь такой: партнёрка не обязана возвращать явное подтверждение; локальный успех = submit прошёл без явной ошибки, дубля, disabled-страницы или невалидной формы. Это подтверждено текущими `modules/platforms/leadsu.py` и `modules/platforms/lovko.py`.
- Product commit `1ab56c867`: Samokat/Lovko disabled-page (`disabled.html`, title/body `Disabled`) классифицируется как `offer_disabled`, а disabled/permanent form failure не попадает в retry queue.

## Проверка после исправления

- Targeted tests:
  - `tests/test_integrations_sync.py tests/test_integrations_partner_api.py tests/test_traffic_tenant_isolation.py -q` -> `20 passed`.
  - `tests/test_leadsu_blank_recovery.py tests/test_platform_success_detection.py tests/test_platform_routing.py tests/test_integrations_sync.py -q` -> `35 passed`.
  - `tests/test_dashboard_realtime_spinner.py tests/test_leadsu_blank_recovery.py tests/test_lovko_success_detection.py tests/test_platform_routing.py tests/test_vbiv_bot_runtime_errors.py tests/test_vbiv_bot_navigation.py -q` -> `54 passed`.
- GitHub Actions:
  - `ff0098114`: `CI` success, `Build and Push Docker Image` success.
  - `87eb74095`: `CI` success, `Build and Push Docker Image` success.
  - `1ab56c867`: проверить через `gh` с авторизацией; на live-сервере `gh` отсутствует, GitHub status API без auth вернул `404`.
- Live deploy:
  - rebuilt/recreated `autolead_bot` and `worker`;
  - `traffichub_app` and `traffichub_worker` healthy;
  - `https://traffic-hub.pro/api/health` -> `status=ok`;
  - container `/app/modules/platforms/leadsu.py` содержит marker `Popup shells alone are not proof`.
  - после `1ab56c867` live `/api/health` -> `status=ok`, `control.backend=postgres`, `control.ok=true`.
- Manual smoke после `185206758`:
  - Тестовый лид `admin / Онекта / 9001617435` завершился `sent=0`, `errors=1`, `status=error`, причина `leadsu: форма не подтверждена после отправки`.
  - В `autolead_send_history` для тестовых телефонов пусто; retry-запись удалена.
  - Live container `/app/modules/platforms/__init__.py` больше не содержит ветку `leadsu + онекта -> tilda`.
- Manual smoke `2026-07-04` по всем admin-офферам, включая inactive, через live `run_campaign()` с временной in-memory конфигурацией:
  - `Дикси` inactive/Lovko -> `sent`.
  - `X5` inactive/Lovko -> `sent`.
  - `Воксис` active/LeadSU -> `sent`.
  - `Онекта` active/LeadSU -> `sent`; логика LeadSU: нет явного partner success, но submit завершился без видимой ошибки, поэтому форма считается заполненной.
  - `ВкусВилл` inactive, фактически LeadSU URL при Lovko-config -> `sent`; локальный успех по отсутствию явной ошибки.
  - `Onecta #2` inactive/Lovko -> `sent`.
  - `Я еда` active/Lovko -> `sent` после снятия vacancy binding в smoke-конфиге.
  - `Ozon` active/Lovko -> `sent`.
  - `Самокат` active/LeadSU tracking -> partner disabled-page; после `1ab56c867` результат `offer_disabled`, причина `samokat: оффер отключен на стороне партнёрки (disabled.html)`, retry queue пропущена.
  - Все smoke-телефоны очищены из `autolead_send_history` и `autolead_retry_queue`.
- Realtime full-cycle UI:
  - `utils/state.py` хранит `current_lead`, `forms_total`, `forms_done`.
  - `modules/vbiv_bot.py` перед каждым оффером пишет `current_lead = "ФИО (телефон)"`, увеличивает `forms_done` после успешной анкеты.
  - `dashboard/app.js` отображает стабильную строку `ФИО (телефон) | анкеты: X/Y`; DOM-node spinner не пересоздаётся, анимация висит только на marker-dot.

## Следующий шаг

- В UI явно разделить две метрики: `Отправлено ботом` из `autolead_send_history` и `Подтверждено партнёркой` из `conversions`/partner API.
- Для контрольного smoke после следующего запуска Autolead проверить новые `admin/Онекта` записи: они не должны попадать в `autolead_send_history.status='sent'`, если Lead.su не вернул явный success/direct-submit success.
- Отдельно доработать Lovko MCP или TrafficHub Lovko scraper для машинной выгрузки конверсий Lovko, потому что текущий MCP подтверждает доступ, но не отдаёт conversions.

Связано: [[2026-06-26 синхронизация LeadSU офферов для конверсий]], [[Lovko sync]], [[03_Ошибки/Отладка/Решённые баги/БАГ-036_false_form_success_lovko_pp_conversions]].
