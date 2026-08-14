# 2026-06-24 Pydantic deprecation debt

## Симптом

Targeted pytest run показывал `PydanticDeprecatedSince20` warnings в TrafficHub API routers и settings.

## Зона системы

- `traffic_hub/api/routers/leads.py`
- `traffic_hub/api/routers/tools.py`
- `traffic_hub/api/routers/finance.py`
- `traffic_hub/api/routers/messengers.py`
- `traffic_hub/api/routers/funnels.py`
- `traffic_hub/config/settings.py`

## Гипотеза

Warnings вызваны использованием Pydantic v1-style `class Config` в моделях и settings при runtime на Pydantic v2.

## Проверка

`grep -R "class Config" traffic_hub api utils services modules` нашёл 6 мест в TrafficHub-коде.

## Наблюдение

После перевода моделей на `ConfigDict(from_attributes=True)` и settings на `SettingsConfigDict(...)` targeted test run в live container показал `28 passed, 2 warnings`. Pydantic warnings исчезли.

## Вывод

Pydantic deprecation debt в нашем TrafficHub-коде закрыт. Оставшиеся warnings относятся к внешним зависимостям/тестовому стеку: `FastAPI/TestClient` и `passlib crypt`.

## Следующий шаг

Не смешивать внешние dependency warnings с product bugs. Планировать отдельно: обновление FastAPI/Starlette/httpx test stack и замену passlib crypt path до Python 3.13.

## Подтверждение

- Commit TrafficHub: `7a6ea8cb7 Migrate TrafficHub pydantic config`.
- Тесты после применения в live container: `28 passed, 2 warnings`.

