# Offer mapping drift confirmed by config merge

Дата: 2026-06-01

Связанные файлы:
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py)
- [utils/control_store.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/control_store.py)
- [tests/test_config_merge.py](C:/Users/Арт/Desktop/TrafServer/remote_files/tests/test_config_merge.py)

## Анализ

При разборе ветки `нет оффера для vacancy_id` подтверждён ещё один системный риск, уже не в retry queue, а в механике конфигурации.

Текущая схема такая:

1. `_shared_config_base(fallback)` собирает базу:
- tenant template
- локальный `config.json`
- shared cloud/control config по HWID

2. `_load_user_config_profile(username, fallback)` затем делает:
- `profile = control_store.load_user_config(username)`
- `return _deep_merge_dicts(base, profile)`

3. `_deep_merge_dicts(...)` для списков делает полную замену, а не smart-merge.

Следствие:
- если в user profile уже есть `offer_mapping: []`
- а в shared base есть рабочий `offer_mapping`
- итоговый runtime config всё равно получит пустой `offer_mapping`

Это не гипотеза по интуиции, а прямое следствие текущего merge-контракта.

## Причина

### 1. User profile полностью перетирает shared `offer_mapping`

- `offer_mapping` — это list
- `_deep_merge_dicts` не умеет merge'ить списки семантически
- значение из `profile` полностью заменяет значение из `base`

Итог:
- пустой или устаревший `offer_mapping` в `user_app_configs`
  может скрыть актуальный shared mapping

### 2. Existing user profiles не ресинхронизируются с shared base

- если профиль уже существует, код не делает selective refresh
- shared-конфиг используется только как base перед overlay профиля
- profile остаётся источником истины, даже если он устарел

Итог:
- изменения shared `offer_mapping` не обязаны доходить до старых user profiles

### 3. Тесты покрывают только seed нового профиля, но не drift существующего

В [test_config_merge.py](C:/Users/Арт/Desktop/TrafServer/remote_files/tests/test_config_merge.py) есть тест:
- новый профиль seed'ится из shared config

Но нет теста на сценарий:
- shared base содержит актуальный `offer_mapping`
- существующий profile содержит пустой/старый `offer_mapping`
- runtime config теряет актуальные офферы

## Критичность

- Критичность: `High`

Потому что последствия идут дальше одного UI-поля:
- `run_full_cycle()` может видеть `has_offers = False`
- `prioritize_leads(...)` может работать по пустому mapping
- retry/send логика может получать leads с `vacancy_id`, но без корректного offer resolution
- это порождает downstream `missing offer`-симптомы

## Последствия

- дрейф поведения между пользователями при одинаковом shared config
- “необъяснимое” отсутствие офферов у отдельных профилей
- накопление terminal retry items
- сложная диагностика: проблема выглядит как баг рассылки, а корень в config merge semantics

## Рекомендуемое исправление

Минимально безопасный путь:

1. Явно определить ownership для `offer_mapping`:
- shared-only
- user-specific
- или гибрид с fallback

2. Если нужен fallback на shared mapping:
- не позволять пустому `profile["offer_mapping"]` затирать непустой shared mapping

3. Добавить тесты на existing-profile drift:
- shared offers present
- profile offers empty
- expected runtime result documented явно

4. Для forensic/operations:
- сравнивать `shared offer_mapping` и `user profile offer_mapping`
- отдельно диагностировать случаи, где user profile зануляет offers
