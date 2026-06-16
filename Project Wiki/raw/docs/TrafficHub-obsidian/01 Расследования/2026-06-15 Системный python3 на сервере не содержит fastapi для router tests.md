# 2026-06-15 Системный `python3` на сервере не содержит `fastapi` для router tests

## Симптом

Попытка прогнать `tests/test_leads_router.py` завершилась на import stage:

- `api.authz`
- `from fastapi import ...`
- `ModuleNotFoundError: No module named 'fastapi'`

## Зона системы

- test environment
- системный `python3` на сервере
- router/API tests

## Гипотеза

Проблема не в `leads` storage split, а в том, что текущий системный интерпретатор сервера не соответствует полному test stack проекта.

## Проверка

Подтверждено на live server:

- `python3 -m pytest -q tests/test_leads_router.py -q` падает на import `fastapi`
- `python3 -c "import importlib.util; print(importlib.util.find_spec('fastapi'))"` возвращает `None`
- в то же время `tests/test_database.py` проходят, то есть storage split сам по себе не сломан

## Наблюдение

- Нельзя использовать системный `python3` на сервере как универсальное доказательство для router/API тестов.
- Для них нужен отдельный bootstrap test environment или контейнер с полным requirements stack.

## Вывод

Это отдельный инфраструктурный дефект test-env, а не баг бизнес-логики или SQLite decomposition.

## Следующий шаг

1. Зафиксировать каноничный способ запуска router/API тестов:
   - в контейнере
   - или в отдельном venv с полным requirements
2. Не смешивать подобные import-time environment errors с регрессиями кода.
