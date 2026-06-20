# БАГ-027 Disabled offer продолжал заполняться из retry queue

## Симптом
Пользователь выключил оффер `Onecta #2` в `Offer Mapping`, но в логах после `Фаза 4: Обработка очереди повторов` появилась строка `Оффер Onecta #2 успешно заполнен`.

## Зона системы
- `dashboard` — toggle `enabled=false` в offer mapping.
- `services/leads_service.py::process_retry_queue` — повторная обработка `retry_queue`.
- `utils.scoring.active_offer_mapping` — фильтрация активных офферов.

## Гипотеза
Обычная рассылка уважает `enabled=false`, но запись, уже лежащая в `retry_queue`, может обходить active offer filter.

## Проверка
Код подтвердил гипотезу:

- `process_retry_queue` строил `offers_by_name` только из active offers;
- если offer не найден в active list, код создавал fallback `base_offer` из старой записи retry queue;
- из-за этого disabled offer, который всё ещё был в конфиге, отправлялся как legacy fallback.

## Наблюдение
Fallback нужен только для старых retry-записей, у которых оффера уже нет в текущем config. Если offer name есть в config, но выключен, это осознанный запрет на отправку.

## Вывод
Каноничное поведение: disabled offer не должен отправляться ни из обычной рассылки, ни из `retry_queue`. Если запись retry queue относится к выключенному offer, она удаляется и считается skipped.

## Исправление
`services/leads_service.py::process_retry_queue` теперь:

- собирает `offer_names_in_config` до фильтрации active offers;
- если `offer_name` есть в config, но отсутствует в active map, удаляет запись из retry queue и не вызывает `run_sender`;
- оставляет legacy fallback только для offer names, которых вообще нет в текущем config.

Регрессия покрыта тестом `tests/test_retry_queue_matching.py::test_process_retry_queue_skips_disabled_configured_offer`.

