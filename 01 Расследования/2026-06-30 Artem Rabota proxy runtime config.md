# 2026-06-30 Artem Rabota proxy runtime config

## Симптом
Нужно поставить прокси для профиля `artem` в TrafficHub без изменения чужих пользователей.

## Зона системы
- PostgreSQL table `control_user_app_configs`
- `services/leads_service.py::load_config()`
- `utils/control_store.py::load_user_config()`
- `api/routers/settings_core.py::normalize_proxy_url()`

## Гипотеза
Прокси Rabota.ru должен храниться в owner-scoped `rabota_ru.proxy_enabled` и `rabota_ru.proxy_url`, а не в глобальном `config.json`.

## Проверка
На live-сервере проверены записи `control_user_app_configs` и runtime-загрузка конфига через `bind_current_username('artem')`.

## Наблюдение
Для `artem` подтверждено:

```text
rabota_ru.proxy_enabled = true
rabota_ru.proxy_url = http://uE0D08:LZCcvM@217.29.62.68:8000
```

`alex` и другие профили не изменялись.

## Вывод
Канонический способ задать прокси пользователю TrafficHub — user-scoped config в PostgreSQL. Формат `host:port:user:pass` нормализуется в HTTP URL; runtime использует итоговый URL для Rabota.ru API и Playwright-заполнения, если `proxy_enabled=true`.

## Следующий шаг
Если прокси не применяется в UI, проверять не SQL-строку, а фактическую загрузку `load_config(force_reload=True)` внутри `bind_current_username(<login>)` и логи `modules/rabota_api.py` / `modules/vbiv_bot.py`.
