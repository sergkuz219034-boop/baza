# Patch-plan: offer mapping drift

Дата: 2026-06-01

Связанные файлы:
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py)
- [tests/test_config_merge.py](C:/Users/Арт/Desktop/TrafServer/remote_files/tests/test_config_merge.py)
- [2026-06-01 offer mapping drift hypothesis confirmed by config merge.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20offer%20mapping%20drift%20hypothesis%20confirmed%20by%20config%20merge.md)

## Анализ

Этот patch-plan касается не runtime retry-механики, а более ранней причины: user profile может занулять shared `offer_mapping`.

## Причина

Сейчас:
- `_load_user_config_profile()` делает полный overlay `profile` поверх `base`
- для списков это означает полную замену

Риск:
- пустой `offer_mapping` из profile скрывает рабочий shared mapping

## План исправления

### Вариант A. Специальное правило для `offer_mapping`

В `_load_user_config_profile()` после merge:
- если `profile.offer_mapping == []`
- и `base.offer_mapping` непустой
- использовать `base.offer_mapping`

Плюсы:
- минимальная правка
- не ломает общую механику merge для других ключей

Минусы:
- special case

### Вариант B. Явная ownership-модель

Определить, что `offer_mapping`:
- либо полностью shared
- либо полностью user-scoped

Плюсы:
- чище архитектурно

Минусы:
- требует больше изменений и миграционного решения

Рекомендуемый путь сейчас:
- вариант A как hotfix-level correctness fix
- вариант B как архитектурное последующее решение

## Diff

Рекомендуемое минимальное направление:

```diff
def _load_user_config_profile(username: str, fallback: dict) -> dict:
    from utils import control_store

    profile = control_store.load_user_config(username)
    base = _shared_config_base(fallback)
    if profile is None:
        control_store.save_user_config(username, base)
        return base

    merged = _deep_merge_dicts(base, profile)

    profile_offers = profile.get("offer_mapping")
    base_offers = base.get("offer_mapping")
    if isinstance(profile_offers, list) and not profile_offers and isinstance(base_offers, list) and base_offers:
        merged["offer_mapping"] = copy.deepcopy(base_offers)

    return merged
```

### Тесты

Нужно добавить тест вроде:

```diff
+ def test_existing_profile_empty_offer_mapping_does_not_blank_shared_offers(...):
+     ...
```

Сценарий:
- shared base содержит непустой `offer_mapping`
- `load_user_config()` возвращает профиль с `offer_mapping: []`
- итоговый runtime config должен сохранить shared offers

## Почему это безопасно

- правка точечная и ограничена одним ключом
- не меняет merge semantics для всех остальных списков
- соответствует реальному operational ожиданию: пустой профиль не должен убивать рабочий mapping без явного намерения

## Побочные эффекты

- если кто-то сознательно использует пустой `offer_mapping` в user profile как способ отключить offers, это поведение изменится
- поэтому нужно отдельно решить: “пустой список” означает “наследовать” или “явно отключить”

На текущих симптомах более вероятно, что пустой список — это drift/устаревание, а не осознанное выключение.

## Проверка после исправления

1. Existing profile с пустым `offer_mapping` больше не теряет shared offers.
2. Новый профиль по-прежнему seed'ится корректно.
3. Пользовательский profile с непустым `offer_mapping` продолжает переопределять shared mapping.

## Дополнительные улучшения

- хранить `offer_mapping` отдельно от общего user config
- ввести tri-state semantics:
  - `unset` → наследовать
  - `[]` → явно отключить
  - `[ ... ]` → переопределить
