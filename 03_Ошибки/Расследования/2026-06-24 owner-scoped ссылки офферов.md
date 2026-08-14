# 2026-06-24 owner-scoped ссылки офферов

## Симптом

Ссылка на анкету/оффер должна принадлежать владельцу анкеты или партнёрки, а не подтягиваться из чужого или устаревшего runtime-state.

## Зона системы

- `services/leads_service.py::process_retry_queue`
- `modules/vbiv_bot.py`
- PostgreSQL `control_user_app_configs.config_json.offer_mapping`
- PostgreSQL `autolead_retry_queue`

## Гипотеза

Обычная рассылка уже берёт `target_url` из owner-scoped `offer_mapping`, но retry queue могла использовать `target_url` из самой retry-записи, если оффер отсутствовал в текущем конфиге владельца.

## Проверка

В `process_retry_queue()` был fallback:

- если `offer_name` не найден среди активных офферов владельца;
- и оффер не найден в текущем конфиге;
- код создавал synthetic `base_offer` из `item.target_url` и `item.platform`.

Это нарушало правило: ссылка должна приходить из owner config, а не из retry runtime row.

## Наблюдение

Исправление `86ee60ef4` убрало fallback на `item.target_url`:

- если оффер отсутствует в конфиге владельца, retry-запись удаляется и пропускается;
- если оффер есть, но выключен, retry-запись удаляется и пропускается;
- если у оффера владельца нет `target_url`, retry-запись удаляется и пропускается;
- `partner/platform` могут быть восстановлены только из owner offer, а не как источник ссылки.

## Вывод

Источник истины для ссылки анкеты/партнёрки — `control_user_app_configs.config_json.offer_mapping` текущего owner. Retry queue хранит техническую попытку повтора, но не является доверенным источником ссылки.

## Следующий шаг

Если появятся другие места, где `target_url` берётся из runtime row, а не из owner config, их нужно переводить на тот же принцип.

## Подтверждение

- Commit TrafficHub: `86ee60ef4 Keep retry offer URLs owner scoped`.
- Regression: `tests/test_retry_queue_matching.py::test_process_retry_queue_does_not_use_retry_target_url_when_offer_missing`.
- Test run: `17 passed`.

