# Config save cross-user drift confirmed

Дата: 2026-06-01

Связанные файлы:
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py)
- [api/routers/settings.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/settings.py)
- [api/routers/offers.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/offers.py)
- [tests/test_config_merge.py](C:/Users/Арт/Desktop/TrafServer/remote_files/tests/test_config_merge.py)

## Анализ

Подтверждён архитектурный риск сохранения конфига:

- почти все runtime-настройки читаются и сохраняются внутри `bind_current_username(...)`
- но `save_config(config)` при наличии текущего пользователя делает **две записи одновременно**:
  1. `control_store.save_user_config(current_username, config)`
  2. `save_config_to_cloud(get_hwid(), config)`

То есть пользовательский конфиг одновременно становится:
- user-scoped конфигом
- и shared HWID-конфигом

Это подтверждено и кодом, и существующим тестом:
- [test_config_merge.py](C:/Users/Арт/Desktop/TrafServer/remote_files/tests/test_config_merge.py) прямо проверяет, что `save_config()` синхронизирует и `user`, и `shared`

## Причина

### 1. User-scoped save одновременно меняет shared base

Сейчас контракт `save_config()` такой:
- если есть `current_username`, сохранить user profile
- затем всё равно сохранить тот же config как shared cloud/HWID config

Это означает, что любой пользовательский runtime-edit:
- `offer_mapping`
- `rabota_ru`
- `vbiv`
- `google_sheets`
- и прочие несекретные настройки

может менять общий конфиг для данного HWID/инстанса.

### 2. Shared base потом участвует в загрузке других профилей

`_shared_config_base(...)` подмешивает shared cloud config в базу для пользователя.

Значит:
- пользователь A может через обычное сохранение изменить shared base
- пользователь B затем получит этот changed shared base при своей загрузке профиля

### 3. В сочетании с overlay user profile это создаёт сложный drift

Получается двойной эффект:

1. user save загрязняет shared base
2. existing user profile затем может:
- либо унаследовать чужие изменения
- либо наоборот перетереть их своим пустым/устаревшим overlay

Именно это делает диагностику `offer_mapping` и других runtime-настроек очень трудной.

## Критичность

- Критичность: `High`

Потому что проблема системная:
- затрагивает не одну очередь и не один endpoint
- влияет на config isolation между пользователями
- может вызывать труднообъяснимый drift поведения

## Последствия

- cross-user pollution конфигурации
- shared `offer_mapping` и user `offer_mapping` перестают иметь ясного владельца
- новые профили seed'ятся из уже загрязнённой shared базы
- часть runtime-проблем может выглядеть случайной, хотя корень — в смешении ownership слоёв

## Рекомендуемое исправление

Минимально безопасная цель:

1. Разделить intent сохранения:
- `save_user_config(...)`
- `save_shared_config(...)`

2. Не писать user-scoped редактирование автоматически в shared HWID-config.

3. Оставить shared save только для явно админских или migration-сценариев.

4. Добавить тесты на ownership:
- user save не меняет shared config по умолчанию
- shared save делается только в явном режиме
