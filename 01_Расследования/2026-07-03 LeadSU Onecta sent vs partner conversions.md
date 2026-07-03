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
- Code facts:
  - `get_owned_summary()` считал `processed_today` и `offers_today` из `autolead_send_history WHERE status='sent'`.
  - `/traffic-api/settings/integrations/leadsu/sync` вызывал `_sync_network(... username=...)` без `tenant_id`, в отличие от Lovko sync.
  - `LeadsuPlatform` передавал в `_wait_success()` слабые popup-shell селекторы `.fancybox-content`, `.fancybox-slide--current`, `[data-fancybox-close]`, которые общий `_wait_success()` принимал как `ok` без проверки текста.

## Наблюдение

TrafficHub UI корректно показывал внутреннюю метрику отправок, но эта метрика не равна партнёрской конверсии. Для `admin/Онекта` подтверждён разрыв: сотни `sent` в Autolead и ноль Lead.su conversions в TrafficHub DB/API-sync.

## Вывод

Root cause состоит из двух частей:

- метрика `Офферы сегодня` в Autolead является internal send-history, а не partner-confirmed conversions;
- Lead.su generic form path мог создавать ложные `sent`, потому что popup-shell считался успехом без явного success text или partner response.

## Исправление

- Product commit `ff0098114`: `sync_leadsu` теперь передаёт `tenant_id=tenant_id_for(current_user)` в `_sync_network`; добавлен тест `test_sync_leadsu_endpoint_passes_current_tenant`.
- Product commit `87eb74095`: generic Lead.su больше не принимает popup-shell selector как доказательство успеха; если явного success нет, код доходит до direct-submit recovery и проверяет ответ партнёрской формы. Добавлен тест `test_leadsu_does_not_treat_popup_shell_as_success`.

## Проверка после исправления

- Targeted tests:
  - `tests/test_integrations_sync.py tests/test_integrations_partner_api.py tests/test_traffic_tenant_isolation.py -q` -> `20 passed`.
  - `tests/test_leadsu_blank_recovery.py tests/test_platform_success_detection.py tests/test_platform_routing.py tests/test_integrations_sync.py -q` -> `35 passed`.
- GitHub Actions:
  - `ff0098114`: `CI` success, `Build and Push Docker Image` success.
  - `87eb74095`: `CI` success, `Build and Push Docker Image` success.
- Live deploy:
  - rebuilt/recreated `autolead_bot` and `worker`;
  - `traffichub_app` and `traffichub_worker` healthy;
  - `https://traffic-hub.pro/api/health` -> `status=ok`;
  - container `/app/modules/platforms/leadsu.py` содержит marker `Popup shells alone are not proof`.

## Следующий шаг

- В UI явно разделить две метрики: `Отправлено ботом` из `autolead_send_history` и `Подтверждено партнёркой` из `conversions`/partner API.
- Для контрольного smoke после следующего запуска Autolead проверить новые `admin/Онекта` записи: они не должны попадать в `autolead_send_history.status='sent'`, если Lead.su не вернул явный success/direct-submit success.
- Отдельно доработать Lovko MCP или TrafficHub Lovko scraper для машинной выгрузки конверсий Lovko, потому что текущий MCP подтверждает доступ, но не отдаёт conversions.

Связано: [[2026-06-26 синхронизация LeadSU офферов для конверсий]], [[Lovko sync]], [[06_Отладка/Решённые баги/БАГ-036_false_form_success_lovko_pp_conversions]].
