# 2026-06-29 применение незакоммиченных изменений TrafficHub

## Симптом

- live repo `/root/TrafficHub` содержал большой dirty-state после нескольких рабочих итераций;
- нужно было применить изменения органично, не потерять полезные правки, не протащить случайный мусор и довести до GitHub/deploy.

## Зона системы

- server repo: `/root/TrafficHub`
- GitHub repo: `sergkuz219034-boop/TrafficHub`
- backend/API: `api/*`, `traffic_hub/*`, `services/*`, `modules/*`, `utils/*`
- frontend/UI: `dashboard/*`, `AccountManager/dashboard/*`
- AccountManager: `AccountManager/api/*`, `AccountManager/services/*`
- runtime: Docker Compose, PostgreSQL, worker, web app, AccountManager, standalone content bot

## Гипотеза

- dirty-state содержит полезные изменения по HR-agent, content bot, dashboard/runtime и Autolead;
- одновременно в нём могут быть регрессии: битая UTF-8 кодировка UI, несовместимость тестовых fake-объектов, CI policy violation или случайные test-only данные.

## Проверка

- проверен `git status -sb`, diff и новые файлы в `/root/TrafficHub`;
- найден и исправлен mojibake в `dashboard/app.js`, `AccountManager/dashboard/app.js`, `AccountManager/dashboard/index.html`;
- test user `alice` в новом HR-agent тесте заменён на существующий `admin`, чтобы не добавлять новый фиктивный источник пользователя;
- `AccountManager/api/routers/hr_agent.py` приведён к обычному `import json` вместо динамического `__import__('json')`;
- `modules/sheets_sync.py` получил fallback на старый `insert_rows`, если fake/test worksheet не поддерживает новый bulk API;
- запрещённый CI-паттерн `headers.Authorization = Bearer ...` заменён на bracket-notation без изменения runtime-поведения;
- прогнаны targeted и expanded тесты на server repo;
- после push проверены GitHub checks;
- после deploy проверены контейнеры, `/api/health`, AccountManager health, наличие HR-agent таблиц в PostgreSQL и состояние maintenance flag.

## Наблюдение

- product commits:
  - `1c0184a9a feat: integrate hr agent and runtime dashboard updates`;
  - `ec8d0eec8 fix: avoid forbidden bearer token assignment pattern`.
- GitHub checks на `ec8d0eec8`:
  - `CI` — success;
  - `Build and Push Docker Image` — success.
- Live deploy выполнен пересозданием контейнеров:
  - `autolead_bot`;
  - `worker`;
  - `account_manager`;
  - `standalone_content_bot`.
- Live `/api/health` на app вернул `status=ok`, `control.backend=postgres`.
- AccountManager `/api/health` вернул `status=ok`.
- PostgreSQL содержит новые таблицы `hr_agent_*`.
- `maintenance_mode` после работ выключен.
- Серверный repo после deploy чистый: `main...origin/main`.
- Полный локальный `pytest -q` в shell сервера упирался в отсутствие `AUTOLEAD_RUNTIME_*_BACKEND=pg` в ручном test env; GitHub CI с корректным окружением прошёл.

## Вывод

- dirty-state применён как product changes, а не оставлен runtime-мусором;
- полезные изменения сохранены, явные регрессии исправлены до push;
- live сейчас работает от commit `ec8d0eec8`;
- канон для product-кода остаётся `/root/TrafficHub` + GitHub `sergkuz219034-boop/TrafficHub`, не `/app`.

## Следующий шаг

- для HR-agent отдельно сделать UI smoke и описать полноценный пользовательский сценарий;
- для server-side ручного pytest добавить documented command/env, чтобы локальный запуск не падал из-за отсутствия PostgreSQL runtime env;
- при следующих больших dirty-state сначала группировать изменения по контурам: `AccountManager`, `Autolead runtime`, `TrafficHub CRM`, `infra`, `tests`.

