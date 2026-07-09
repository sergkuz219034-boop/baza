# 2026-07-09 admin offer_mapping wiped by partial user-config save

## Симптом

У `admin` после перезапуска / очередного сохранения конфига пропадают привязанные офферы: в `control_user_app_configs` поле `offer_mapping` становится пустым, хотя раньше в UI были заполненные офферы.

## Зона системы

- owner-scoped config persistence
- `services/leads_service.py`
- `utils/control_store.py`
- `api/routers/settings.py`
- `api/routers/offers.py`
- `traffic_hub/services/autolead_bridge.py`

## Гипотеза

Пользовательский конфиг сохраняется целиком через `save_user_config()`, и один из путей записи передаёт профиль без `offer_mapping` или с пустым списком. Из-за full overwrite это стирает текущие офферы для владельца.

## Проверка

- live `control_user_app_configs.admin` в PostgreSQL: `offer_count=0`, `updated_at=2026-07-04 23:29:39 Europe/Moscow`.
- `services/leads_service.py::save_config()` вызывает `control_store.save_user_config(current_username, config)` без частичного патча.
- `utils/control_store.py::save_user_config()` раньше делал полный `INSERT ... ON CONFLICT DO UPDATE SET config_json=excluded.config_json`.
- `api/routers/settings.py` и `traffic_hub/api/routers/integrations.py` сохраняют конфиг через тот же owner-scoped save-path.
- `api/routers/offers.py` и `traffic_hub/services/autolead_bridge.py` действительно должны уметь очищать список офферов, но только явно через offer-management пути.

## Наблюдение

Последний live-save для `admin` произошёл в `2026-07-04 23:29:39`, после чего `offer_mapping` в control store остался пустым. Это совпадает с записью в логах `Пользовательский конфиг сохранён для admin`.

## Вывод

Причина не в самом перезапуске. Перезапуск только поднял уже сохранённое состояние из PostgreSQL. Реальный источник потери — full overwrite пользовательского конфига без защиты `offer_mapping` от неполных settings-save.

## Следующий шаг

Оставить в codebase invariant: обычные settings-save пути не должны очищать существующие офферы. Очистка `offer_mapping` должна проходить только через явные offer-management операции.
