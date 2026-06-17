# Wave 2 execution pack: config ownership split

Дата: 2026-06-01

Связанные документы:
- [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
- [2026-06-01 wave-by-wave validation checklist.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave-by-wave%20validation%20checklist.md)
- [2026-06-01 patch-plan config save ownership split.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20config%20save%20ownership%20split.md)
- [2026-06-01 config save cross-user drift confirmed.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20config%20save%20cross-user%20drift%20confirmed.md)

## Анализ

Этот execution-pack покрывает `Wave 2`: остановка нового config drift через разделение user-save и shared-save.

Подтверждённые факты по текущему коду:

- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py:400)
  - `save_config(config)` сейчас:
    - сохраняет user profile
    - сохраняет local config
    - и затем всё равно пишет shared HWID-config

- текущие call sites `save_config(...)`:
  - [api/routers/offers.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/offers.py:111)
  - [api/routers/offers.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/offers.py:350)
  - [api/routers/settings.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/settings.py:551)
  - [api/routers/settings.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/settings.py:572)
  - [api/routers/settings.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/settings.py:590)
  - [api/routers/settings.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/settings.py:627)
  - [api/routers/settings.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/settings.py:685)
  - [api/routers/settings.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/settings.py:706)

Наблюдение:
- все эти вызовы происходят в user-facing flows внутри `bind_current_username(...)`
- среди них нет очевидного административного shared-template workflow

Предварительный вывод:
- для этих call sites безопаснее считать целевым режимом `sync_shared=False`
- shared save должен остаться только для отдельного, явно выделенного пути

## Причина

### 1. Текущий контракт `save_config()` слишком широкий

- одна функция делает три действия сразу:
  - user save
  - local save
  - shared save

Это и есть первопричина cross-user drift.

### 2. User-facing endpoints не выглядят как rightful owners shared config

По текущему коду:
- patch обычных настроек
- patch operator settings
- superjob patch
- offer import/edit
- vacancy aliases
- spreadsheet name refresh
- settings bundle import

все выглядят как user/runtime-операции, а не как shared-template administration.

### 3. Shared save уже имеет отдельные низкоуровневые точки в другом слое

- [utils/control_store.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/control_store.py:273) содержит explicit `save_config(hwid, cfg)`
- [utils/license.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/license.py:945)
- [utils/license.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/license.py:990)

То есть shared-path как инфраструктурная возможность уже существует и не обязан висеть на каждом user save.

## План исправления

### Шаг 1. Изменить сигнатуру `save_config()`

Рекомендуемый переходный контракт:

```diff
- def save_config(config: dict) -> None:
+ def save_config(config: dict, sync_shared: bool = False) -> None:
```

### Шаг 2. Убрать shared sync из default path

```diff
- save_config_to_cloud(get_hwid(), config)
+ if sync_shared:
+     save_config_to_cloud(get_hwid(), config)
```

### Шаг 3. Явно пройти по call sites

Рекомендуемая классификация на текущем этапе:

- `offers.py:_persist_offer_mapping(...)`
  - `sync_shared=False`
- `offers.py:/import`
  - `sync_shared=False`
- `settings.py:/superjob`
  - `sync_shared=False`
- `settings.py:/patch`
  - `sync_shared=False`
- `settings.py:/operator` and `/user`
  - `sync_shared=False`
- `settings.py:/import`
  - `sync_shared=False` на этом этапе, если import трактуется как пользовательский settings bundle
- `settings.py:_refresh_spreadsheet_names(...)`
  - `sync_shared=False`
- `settings.py:/vacancy-aliases`
  - `sync_shared=False`

### Шаг 4. Обновить тестовый контракт

Текущий тест:
- `test_save_config_syncs_user_local_and_shared_targets`

Нужно изменить на:
- user save обновляет user/local
- shared target не трогается по умолчанию

И добавить отдельный тест:
- `save_config(config, sync_shared=True)` действительно пишет shared target

## Diff

### Изменение сигнатуры

```diff
# remote_files/services/leads_service.py
- def save_config(config: dict) -> None:
+ def save_config(config: dict, sync_shared: bool = False) -> None:
```

### Изменение shared-save поведения

```diff
-     try:
-         from utils.license import get_hwid, save_config_to_cloud
-
-         save_config_to_cloud(get_hwid(), config)
-     except Exception as e:
-         logger.debug("Синхронизация общего конфига не удалась: %s", e)
+     if sync_shared:
+         try:
+             from utils.license import get_hwid, save_config_to_cloud
+
+             save_config_to_cloud(get_hwid(), config)
+         except Exception as e:
+             logger.debug("Синхронизация общего конфига не удалась: %s", e)
```

### Изменение user-facing call sites

```diff
# remote_files/api/routers/offers.py
- save_config(config)
+ save_config(config, sync_shared=False)
```

```diff
# remote_files/api/routers/settings.py
- save_config(config)
+ save_config(config, sync_shared=False)
```

```diff
# remote_files/api/routers/settings.py
- save_config(fresh)
+ save_config(fresh, sync_shared=False)
```

### Изменение тестов

```diff
# remote_files/tests/test_config_merge.py
- def test_save_config_syncs_user_local_and_shared_targets(...):
+ def test_save_config_syncs_user_and_local_targets_by_default(...):
```

```diff
- assert calls["shared"][0] == "hwid-1"
+ assert "shared" not in calls
```

И добавить:

```diff
+ def test_save_config_syncs_shared_target_when_explicitly_requested(...):
+     ...
+     leads_service.save_config(config, sync_shared=True)
+     assert calls["shared"][0] == "hwid-1"
```

## Почему это безопасно

1. Shared save не удаляется, а переводится в explicit mode.
2. User-facing flows начинают делать то, что логически и обещают: менять пользовательский/runtime конфиг, а не общий shared template.
3. Изменение узкое и хорошо покрывается точечными unit tests.

## Побочные эффекты

### Ожидаемые

- user edits перестанут автоматически распространяться в shared HWID-config
- новые user profiles перестанут seed'иться из “случайно загрязнённой” shared базы

### Возможные скрытые

- если какой-то внешний operational workflow неявно полагался на old behavior, он перестанет видеть auto-propagation
- settings bundle import админом может ожидаться как shared operation; это нужно отдельно зафиксировать политикой продукта

## Проверка после исправления

### Обязательные проверки

1. User save:
- обновляет `user_app_configs`
- обновляет local config
- не трогает shared HWID-config

2. Explicit shared save:
- всё ещё работает при `sync_shared=True`

3. Offer editing/import:
- не создаёт shared drift

4. Settings patch/import:
- не меняет shared template без явного намерения

5. Тесты:
- default-path test обновлён
- explicit-shared test добавлен

## Открытый вопрос

Нужно явно принять продуктовое решение по `settings import`:

- это user-scoped restore
  или
- это shared-template administration

Пока более безопасное предположение:
- считать его user-scoped и оставлять `sync_shared=False`

До явного подтверждения обратного не стоит автоматически возвращать shared overwrite.
