# 2026-06-26 Пампаду только postback без API token

## Симптом
В настройках TrafficHub для Пампаду отображалось поле `API TOKEN`, хотя у Пампаду в текущей модели нет API token: используется только postback URL.

## Зона системы
[[TrafficHub Partner Integrations]], `dashboard/app.js`, `dashboard/traffic/index.html`, `traffic_hub/api/routers/integrations.py`, live container `traffichub_app`.

## Гипотеза
UI и API унаследовали Пампаду от token-based интеграции и считали сеть настроенной только при наличии `credentials.token`.

## Проверка
На сервере `/root/TrafficHub` найдено:
- `dashboard/app.js`: `pampadu` был описан как `credential: token`;
- `dashboard/traffic/index.html`: старый экран показывал `Pampadu token` и отправлял `pampadu_token`;
- `traffic_hub/api/routers/integrations.py`: `_runtime_credentials()` читал `settings.pampadu_api_token`, `_integration_status()` требовал token.

## Наблюдение
Пампаду уже есть в postback-контуре: `OfferNetwork.pampadu` входит в `_POSTBACK_NETWORKS`, `/traffic-api/postbacks/pampadu` принимает конверсии по postback token.

## Вывод
Для Пампаду источник истины настройки - наличие сгенерированного postback URL, а не API credential.

## Что изменено
- Убран token input Пампаду из основного dashboard.
- Убран token input Пампаду из старого `/traffic` dashboard.
- Dashboard больше не отправляет `pampadu_token` при сохранении настроек.
- Backend больше не берёт `pampadu_api_token` из runtime settings.
- Публичный статус Пампаду теперь `configured`, если есть postback token.
- Live container `traffichub_app` пересобран и проверен как healthy.
- Server repo зафиксирован commit `3fd3f611b`.

## Следующий шаг
Если Пампаду снова покажет credential input, первый check — `CRM_NETWORK_META.pampadu.credential` в `dashboard/app.js`: ожидается `postback_only`.
