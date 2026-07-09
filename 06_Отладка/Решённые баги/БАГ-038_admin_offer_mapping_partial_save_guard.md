# БАГ-038 admin offer_mapping partial save guard

## Симптом

У `admin` после очередного сохранения конфига / перезапуска сервера офферы исчезали из `offer_mapping`.

## Проверка

- live `control_user_app_configs.admin` в PostgreSQL: `offer_count=0`, `updated_at=2026-07-04 23:29:39 Europe/Moscow`.
- `services/leads_service.py::save_config()` пишет user config через `control_store.save_user_config(current_username, config)`.
- `utils/control_store.py::save_user_config()` делал полный overwrite `config_json`.
- `api/routers/offers.py` и `traffic_hub/services/autolead_bridge.py` тоже пишут `offer_mapping`, поэтому им нужен явный escape hatch для пустого списка.

## Исправление

- `utils/control_store.py` теперь защищает существующий `offer_mapping` от неполного user-config save.
- `api/routers/offers.py` и `traffic_hub/services/autolead_bridge.py` помечают намеренный empty-write через `_allow_empty_offer_mapping=True`.
- Добавлены regression tests в `tests/test_config_merge.py`.

## Вывод

Это общий persistence-bug, а не проблема только `admin`. Без защиты любой settings-save без `offer_mapping` мог стереть офферы у любого пользователя.

## Residual risk

Если появится новый путь записи user-config вне текущих routers/services, он должен либо передавать `offer_mapping`, либо явно маркировать намеренное очищение.
