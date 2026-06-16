# 2026-06-15 Добавлено прямое test coverage для `autofit_seen`

## Симптом

Перед выделением `autofit_seen` из `utils/database.py` прямого test coverage почти не было:

- были только косвенные monkeypatch usage;
- не было узких проверок на:
  - добавление `resume_id`
  - игнор дублей
  - очистку `autofit_seen`

## Зона системы

- `tests/test_database.py`
- `utils/database.py`
- `autofit_seen`

## Гипотеза

Без прямых unit tests следующий storage split будет опираться только на compile и ручной reasoning, что слишком слабо для operational state блока.

## Проверка

В `tests/test_database.py` добавлены прямые тесты:

- `test_mark_and_get_seen_autofit_resume_ids`
- `test_mark_autofit_seen_ignores_duplicates`
- `test_clear_autofit_seen`

После добавления:

- `python3 -m pytest -q tests/test_database.py -q`

## Наблюдение

- Новые tests проходят.
- `autofit_seen` получил минимально достаточное прямое покрытие для безопасного decomposition.

## Вывод

Это не просто test-addition, а подготовительный инженерный шаг перед split runtime storage.

## Следующий шаг

1. Выделить `autofit_seen` в отдельный internal module.
2. После split повторно прогнать `tests/test_database.py`.
