# 2026-06-30 AccountManager live check

## Симптом

Нужно проверить, "что не так" с live `AccountManager`, потому что внешний вход мог выглядеть как сломанный.

## Зона системы

- `/root/TrafficHub/AccountManager/api/main.py`
- `/root/TrafficHub/deploy/Caddyfile`
- контейнеры `traffichub_account_manager`, `traffichub_caddy`, `traffichub_app`
- домены `am.traffic-hub.pro`, `traffic-hub.pro`

## Гипотеза

Возможны три варианта:

- сломан сам `AccountManager`;
- `401` на `am.traffic-hub.pro` является штатной защитой entrypoint;
- проблема находится не в `AccountManager`, а в основном backend-контуре `traffic-hub.pro`.

## Проверка

- На live host подтверждены:
  - `traffichub_account_manager` — `healthy`;
  - `traffichub_caddy` — `up`;
  - `traffichub_app` и `traffichub_worker` к моменту проверки тоже `healthy`.
- `curl http://127.0.0.1:8124/api/health` вернул `{"status":"ok"}`.
- `curl -I https://am.traffic-hub.pro/` вернул `HTTP/2 401`.
- Прямой `GET https://am.traffic-hub.pro/` тоже вернул `{"detail":"Unauthorized"}`.
- В `AccountManager/api/main.py` middleware подтверждает, что без `Bearer`/`token`/`access_token`:
  - HTML-запросы редиректятся на login только если `Accept` содержит `text/html`;
  - остальные запросы получают `401`.
- В тех же live-логах `AccountManager` есть обычные успешные запросы:
  - `GET / -> 200`
  - `GET /static/* -> 200`
  - `GET /api/* -> 200`
  Это подтверждает, что UI работает при валидной auth-сессии.
- В логах `traffichub_caddy` найдены не ошибки `AccountManager`, а `502` на `traffic-hub.pro`:
  - `dial tcp 172.22.0.5:8080: connect: connection refused`
  - `lookup autolead_bot on 127.0.0.11:53: no such host`
- Во время повторной проверки основной контейнер уже снова поднят:
  - `traffichub_app` — `healthy`
  - `curl http://127.0.0.1:8080/api/health` -> `status=ok`

## Наблюдение

- `AccountManager` не выглядит упавшим: health зелёный, scheduler жив, API отвечает.
- Внешний `401` на `am.traffic-hub.pro` сам по себе не доказывает поломку: это protected entrypoint.
- Подозрительный runtime drift был в основном приложении `traffic-hub.pro`, а не в `AccountManager`: Caddy видел временные `502` до `autolead_bot`.
- Server repo `/root/TrafficHub` при этом остаётся грязным по нескольким файлам, включая `AccountManager/*`, поэтому runtime и git-state нельзя считать полностью синхронизированными без отдельного deploy-решения.

## Вывод

На момент проверки `AccountManager` как сервис работает. Реальная проблема из собранных evidence:

- не "сломанный AccountManager",
- а то, что его public entry защищён и без токена отдаёт `401`,
- плюс рядом был отдельный transient/runtime-сбой основного `autolead_bot`, из-за которого `traffic-hub.pro` ловил `502`.

## Следующий шаг

- Если symptom у пользователя именно "не открывается `AccountManager`", нужно проверять способ входа:
  - через штатный token bootstrap из `TrafficHub`;
  - либо через admin-сессию/cookie.
- Если symptom был про `traffic-hub.pro`, расследование нужно продолжать уже по `autolead_bot` restart/drift, а не по `AccountManager`.
- Отдельно разобрать грязный server repo и подтвердить, какие из несохранённых `AccountManager/*` изменений уже реально задеплоены, а какие нет.
