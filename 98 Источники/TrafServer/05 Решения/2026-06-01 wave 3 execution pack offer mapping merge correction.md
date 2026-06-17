# Wave 3 execution pack: offer mapping merge correction

Дата: 2026-06-01

Связанные документы:
- [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
- [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)
- [2026-06-01 patch-plan offer mapping drift.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20offer%20mapping%20drift.md)
- [2026-06-01 offer mapping drift hypothesis confirmed by config merge.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20offer%20mapping%20drift%20hypothesis%20confirmed%20by%20config%20merge.md)
- [2026-06-01 wave 2 execution pack config ownership split.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%202%20execution%20pack%20config%20ownership%20split.md)

## Анализ

Этот execution-pack покрывает `Wave 3`: исправление merge-semantics для `offer_mapping` после того, как `Wave 2` остановит генерацию нового shared drift.

Подтверждённые факты по текущему коду:

- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py:38)
  - `_deep_merge_dicts(...)` для list-полей делает полную замену
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py:131)
  - `_shared_config_base(...)` собирает shared base
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py:151)
  - `_load_user_config_profile(...)` делает overlay `profile` поверх `base`
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py:159)
  - возвращает `_deep_merge_dicts(base, profile)` без special-case для `offer_mapping`

Имеем прямое следствие:
- если `base["offer_mapping"]` непустой
- а `profile["offer_mapping"] == []`
- итоговый runtime config получает `[]`

Тестовое покрытие сейчас:
- [tests/test_config_merge.py](C:/Users/Арт/Desktop/TrafServer/remote_files/tests/test_config_merge.py)
  - покрывает seed нового профиля
  - не покрывает drift existing profile с пустым `offer_mapping`

## Причина

### 1. Merge semantics list-полей слишком грубая для `offer_mapping`

Сейчас список в `profile` полностью заменяет список в `base`.

Для многих полей это допустимо, но для `offer_mapping` создаёт отдельный классовый drift.

### 2. `offer_mapping` — не просто “ещё одно поле config”

Оно участвует в:
- `has_offers`
- `prioritize_leads(...)`
- retry resend path
- downstream offer resolution

Поэтому пустой overlay не просто меняет UI-настройку, а ломает runtime-поведение.

### 3. Без `Wave 2` этот фикс был бы нестабилен

Если не отделить user-save от shared-save заранее:
- даже после merge-fix новый drift продолжит записываться обратно в shared base

## План исправления

### Шаг 1. Не менять общий `_deep_merge_dicts()` глобально

Самый безопасный путь:
- не вводить общий “умный merge для всех списков”
- сделать специальное правило для `offer_mapping`

Это уменьшает риск побочных эффектов на других list-полях.

### Шаг 2. Исправить `_load_user_config_profile(...)`

Переходная логика:

1. Сначала выполнить обычный merge.
2. Потом отдельно решить судьбу `offer_mapping`.

Рекомендуемое правило:
- если `profile.offer_mapping` — пустой list
- и `base.offer_mapping` — непустой list
- вернуть `base.offer_mapping`

### Шаг 3. Добавить regression-тесты

Минимум два теста:

1. existing profile with empty offers does not blank shared offers
2. existing profile with non-empty offers still overrides shared offers

## Diff

### 1. Локальный special-case в `_load_user_config_profile()`

```diff
# remote_files/services/leads_service.py
def _load_user_config_profile(username: str, fallback: dict) -> dict:
    from utils import control_store

    profile = control_store.load_user_config(username)
    base = _shared_config_base(fallback)
    if profile is None:
        control_store.save_user_config(username, base)
        return base
-   return _deep_merge_dicts(base, profile)
+   merged = _deep_merge_dicts(base, profile)
+
+   profile_offers = profile.get("offer_mapping")
+   base_offers = base.get("offer_mapping")
+   if isinstance(profile_offers, list) and not profile_offers and isinstance(base_offers, list) and base_offers:
+       merged["offer_mapping"] = copy.deepcopy(base_offers)
+
+   return merged
```

### 2. Тест: пустой profile не убивает shared offers

```diff
# remote_files/tests/test_config_merge.py
+ def test_existing_profile_empty_offer_mapping_does_not_blank_shared_offers(monkeypatch):
+     monkeypatch.setattr(leads_service, "_shared_config_base", lambda fallback: {
+         "offer_mapping": [{"name": "Offer A", "target_url": "https://a", "platform": "rabota", "vacancy_ids": [1], "vacancy_names": []}],
+     })
+     monkeypatch.setattr("utils.control_store.load_user_config", lambda username: {"offer_mapping": []})
+     profile = leads_service._load_user_config_profile("alice", {})
+     assert profile["offer_mapping"]
```

### 3. Тест: непустой profile всё ещё переопределяет shared offers

```diff
+ def test_existing_profile_nonempty_offer_mapping_overrides_shared_offers(monkeypatch):
+     ...
+     assert profile["offer_mapping"][0]["name"] == "User Offer"
```

## Почему это безопасно

1. Правка точечная и ограничена только `offer_mapping`.
2. Не меняется общая merge semantics для других списков.
3. Изменение идёт после `Wave 2`, где уже прекращён новый shared drift.

## Побочные эффекты

### Ожидаемые

- часть пользователей с пустым/устаревшим profile внезапно “увидит обратно” shared offers
- это ожидаемый эффект исправления drift

### Возможные скрытые

- если product-смысл пустого `offer_mapping` был “явно отключить offers”, это поведение изменится

Именно поэтому нужен явный продуктовый инвариант.

## Проверка после исправления

### Обязательные проверки

1. Existing profile с пустым `offer_mapping` больше не теряет shared offers.
2. Existing profile с непустым `offer_mapping` продолжает переопределять shared base.
3. Новый профиль по-прежнему seed'ится корректно.
4. Regression-тесты добавлены и описывают семантику явно.

## Открытый вопрос

Нужно окончательно определить семантику пустого списка:

- `[]` = наследовать shared offers
  или
- `[]` = явно отключить offers

Пока по текущим симптомам более безопасная рабочая трактовка:
- пустой список у existing profile чаще является drift/legacy artifact, а не осознанной командой “отключить offers”.
