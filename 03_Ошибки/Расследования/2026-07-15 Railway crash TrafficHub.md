# Railway crash TrafficHub

## Симптом

GitHub-connected deployment Railway для сервиса `TrafficHub` завершался статусом `CRASHED`. GitHub Actions при этом были зелёными.

## Зона системы

Root `Dockerfile`, `main.py`, Railway deployment и production-only требования Autolead runtime.

## Гипотеза

Railway запускал root image вне Docker Compose, поэтому процесс не получал обязательные compose-переменные и не слушал выданный платформой `PORT`.

## Проверка

- В repo отсутствовали `railway.toml`, `railway.json`, `Procfile` и Nixpacks config.
- Root image выполнял `python main.py`; default bind был `127.0.0.1:8080`, переменная `PORT` не использовалась.
- Воспроизведение image с `RAILWAY_ENVIRONMENT=production` и без compose env завершилось ошибкой требования PostgreSQL backend для logs, delivery, leads, autofit, invites и control sync.
- Первый адаптер Railway исправил bind/`PORT`, но deployment упал по healthcheck через 5 минут: в Railway отсутствовали `DATABASE_URL` и/или `SESSION_SECRET_KEY`.

## Наблюдение

Production compose остаётся каноническим полным runtime. Railway-проект подключён к GitHub, но не имеет собственного PostgreSQL/session contour.

## Вывод

Причина не в коммите Audience Parser: Railway пытался запустить production runtime без его инфраструктурных зависимостей. Product commits `0f2e2b086` и `8dcd3ee02` добавили явный Railway adapter. При наличии `DATABASE_URL` и `SESSION_SECRET_KEY` запускается полный runtime с PostgreSQL-only backend. При их отсутствии запускается безопасный gateway: `/api/health` сообщает `mode=gateway`, остальные пути перенаправляются на `https://traffic-hub.pro`.

## Следующий шаг

Если Railway должен стать самостоятельным полным production contour, подключить PostgreSQL, задать `DATABASE_URL` и `SESSION_SECRET_KEY`, затем проверить миграции и persistence. До этого канонический продукт обслуживается Docker Compose на live host.

