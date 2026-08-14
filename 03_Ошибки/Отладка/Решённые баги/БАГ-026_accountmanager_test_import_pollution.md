# БАГ-026: AccountManager test import pollution

## Симптом
Полный `pytest` внутри `autolead_server_bot` падал на collection с ошибками вида:

- `ImportError: cannot import name 'offers' from 'api.routers' (/app/AccountManager/api/routers/__init__.py)`
- `ModuleNotFoundError: No module named 'utils.state'`
- `ModuleNotFoundError: No module named 'services.leads_service'`

При этом целевые тесты TrafficHub проходили, а live runtime был здоров.

## Зона системы
Тестовая инфраструктура product repo `sergkuz219034-boop/TrafficHub`:

- `tests/test_account_manager_content.py`
- корневые short-imports `api`, `services`, `utils`, `config`
- вложенный контур `AccountManager`

## Гипотеза
Один из тестов AccountManager меняет `sys.path` глобально на этапе collection, из-за чего остальные тесты TrafficHub начинают импортировать `api/services/utils` из `AccountManager`, а не из основного приложения.

## Проверка
На live:

- server repo: `/root/TrafficHub`
- commit до фикса: `1a9462b04`
- `docker exec autolead_server_bot pytest -q` падал на collection
- `tests/test_account_manager_content.py` содержал top-level `sys.path.insert(0, AccountManager)` и удаление корня repo из `sys.path`

## Наблюдение
Проблема не была runtime-регрессией пользователей. Это был невалидный полный тестовый запуск: тест AccountManager загрязнял процесс pytest до запуска остальных тестов.

## Вывод
Глобальные изменения `sys.path` в тестах запрещены. Если нужно тестировать direct-entry imports AccountManager, переключение import path должно быть локальным и восстанавливаться после теста.

## Исправление
В commit `d038ad5a1` тест `tests/test_account_manager_content.py` переведён на fixture:

- сохраняет исходные `sys.path` и `sys.modules`;
- временно подставляет `AccountManager` root;
- импортирует нужные модули;
- после теста восстанавливает import state.

## Проверка после исправления
В контейнере `autolead_server_bot`:

```text
281 passed, 43 skipped
```

Live health:

- `autolead_server_bot` healthy
- `traffichub_worker` healthy
- `traffichub_account_manager` healthy
- `/api/health` возвращает `status=ok`, `control.backend=postgres`
- ошибок в `autolead_server_bot` за последние 30 минут не найдено

## Следующий шаг
Если добавляются новые тесты для вложенных контуров (`AccountManager`, license services), не менять `sys.path` на уровне module import. Использовать subprocess или fixture с гарантированным восстановлением import state.
