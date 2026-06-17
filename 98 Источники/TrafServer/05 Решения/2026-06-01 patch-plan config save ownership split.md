# Patch-plan: config save ownership split

Дата: 2026-06-01

Связанные файлы:
- [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_files/services/leads_service.py)
- [tests/test_config_merge.py](C:/Users/Арт/Desktop/TrafServer/remote_files/tests/test_config_merge.py)
- [2026-06-01 config save cross-user drift confirmed.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20config%20save%20cross-user%20drift%20confirmed.md)

## Анализ

Текущая проблема не в одном endpoint, а в ownership-контракте `save_config()`.

Сейчас:
- user save
- local file save
- shared cloud save

происходят одним вызовом.

## Причина

Нельзя надёжно держать user-scoped и shared-scoped конфиг, если одна и та же функция всегда пишет в оба места.

## План исправления

### Вариант A. Разделить функции сохранения

Рекомендуемый путь:

- `save_config(config)` → user/local save only
- новая функция `save_shared_config(config)` → явный shared save

Плюсы:
- прозрачный ownership
- меньше скрытых side effects

### Вариант B. Флаг режима в `save_config()`

Например:

- `save_config(config, sync_shared=False)`

Плюсы:
- меньше переписывать call sites

Минусы:
- ownership остаётся менее явным

Рекомендуемый путь:
- вариант B как минимальный безопасный переход
- потом вариант A как архитектурная чистка

## Diff

Минимальный переходный вариант:

```diff
- def save_config(config: dict) -> None:
+ def save_config(config: dict, sync_shared: bool = False) -> None:
```

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

Тогда обычные user-facing роуты:

```diff
- save_config(config)
+ save_config(config, sync_shared=False)
```

А редкие admin/migration сценарии:

```diff
+ save_config(config, sync_shared=True)
```

## Почему это безопасно

- правка не ломает формат конфига
- меняется только маршрут сохранения
- по умолчанию убирается самый опасный side effect: user save -> shared overwrite

## Побочные эффекты

- новые shared изменения больше не будут автоматически распространяться через обычные user edits
- если какая-то часть системы неявно рассчитывала на такое распространение, она перестанет его получать

Это скорее полезное вскрытие скрытой зависимости, чем новый дефект.

## Проверка после исправления

1. User save обновляет:
- user profile
- local `config.json`

но не shared HWID config.

2. Shared config меняется только в явном admin/migration сценарии.

3. Existing tests нужно обновить:
- текущий `test_save_config_syncs_user_local_and_shared_targets` больше не должен ожидать shared save по умолчанию

4. Добавить новый тест:
- user save does not touch shared target unless `sync_shared=True`

## Дополнительные улучшения

- ввести отдельные API/сервисы:
  - user config service
  - shared template service
- логировать ownership save-path явно:
  - `saved user config`
  - `saved shared config`
