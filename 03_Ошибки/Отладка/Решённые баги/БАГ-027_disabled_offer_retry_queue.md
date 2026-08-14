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

## Дополнение 2026-06-21

### Симптом
После фикса пользователь снова увидел старое поведение: `Onecta #2` был выключен у `admin`, но в runtime оставались записи `admin/Onecta #2` в `autolead_retry_queue`.

### Проверка
Live inspection подтвердил:

- `/root/TrafficHub` и контейнер `/app` были на актуальном commit с фиксом `0d1663fd8`;
- публичный frontend отдавал свежие `app.js/style.css` с `no-cache`;
- `admin` config действительно имел `Onecta #2 enabled=False`;
- PostgreSQL `autolead_retry_queue` всё ещё содержал `17` записей `admin/Onecta #2`.

### Наблюдение
Фикс `process_retry_queue` запрещал отправку выключенного оффера на следующей фазе 4, но не удалял уже накопленный хвост очереди в момент выключения оффера. Это выглядело как возврат старого бага.

### Исправление
Commit `adc94caad` добавил purge retry queue при изменении offer mapping:

- `api/routers/offers.py::update_offer_enabled` удаляет retry-записи по offer name при `enabled=false`;
- `api/routers/offers.py::delete_offer` удаляет retry-записи по удалённому offer name;
- `utils.database.remove_offer_from_retry_queue`;
- `utils/runtime_store_pg_delivery.remove_offer_from_retry_queue`;
- `utils/runtime_store_delivery.remove_offer_from_retry_queue`.

На live вручную очищен старый хвост `admin/Onecta #2`: удалено `17` записей.

### Проверка после исправления

- targeted tests: `32 passed`;
- full tests in live image: `286 passed, 43 skipped`;
- GitHub checks для `adc94caad`: `CI` success, `Build and Push Docker Image` success;
- live health: `200`;
- свежие docker logs за 15 минут: без `traceback/exception/error/ошибка`.
