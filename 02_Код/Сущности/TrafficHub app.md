# TrafficHub app

## Legacy dashboard

После commit `fd205a4fe` старый `/traffic/*` не считается рабочим UI-контуром. Он оставлен только как backward-compatible redirect в основной dashboard.

Канонический UI для раздела `TrafficHub` находится внутри основного dashboard и открывается через hash routes `#crm-*`.

После commit `4873a176b` hash routes `#crm-*` мапятся на отдельные tab-pane, а не на Autolead-разделы:

- `#crm` -> `tab-crm-overview`
- `#crm-leads` -> `tab-crm-leads`
- `#crm-messengers` -> `tab-crm-messengers`
- `#crm-funnels` -> `tab-crm-funnels`
- `#crm-networks` -> `tab-crm-networks`
- `#crm-finance` -> `tab-crm-finance`
- `#crm-analytics` -> `tab-crm-analytics`
- `#crm-settings` -> `tab-crm-settings`

Это важно для UX: раздел `TrafficHub` больше не должен показывать Autolead `leads/offers/stats/settings` под CRM-названиями.

См. [[TrafficHub legacy dashboard отключён]].

Теги: #сущность

## Тип

Модуль

## Где находится

`remote_files/traffic_hub/app.py`

## Роль в системе

Регистрирует TrafficHub routers, выполняет миграции и поднимает websocket endpoints. Это точка сборки business API-контурa.

## Входы

- FastAPI app
- роутеры и websocket manager

## Выходы

- `/traffic-api/*`
- `/traffic-ws`
- `/ws`
- основной dashboard `/#crm-*`
- backward-compatible redirect `/traffic/*` -> `/#crm-*`

## Зависимости

- [[TrafficHub database]]
- [[API]]

## Типовые сбои или риски

- router imports расходятся с доступным snapshot;
- неполный локальный source coverage.
- повторное смешивание `crm-*` с Autolead tab-pane приведёт к тому, что пользователь увидит не тот раздел при клике в sidebar.

## Состояние репозитория на 2026-10-01

Каноническая ветка `main` репозитория `sergkuz219034-boop/TrafficHub` указывает на commit `1b7a2dbb` (`Handle oversized HH negotiation identifiers`). Последняя серия изменений добавила:

- официальный HH employer OAuth с сохранением owner-scoped контекста до callback;
- ручной обмен HH authorization code и импорт ответов HH с отображением прогресса job;
- запуск runtime build после HH-импорта;
- защиту от слишком больших negotiation identifiers;
- immutable deploy dashboard через production release-контур.

Проверяемые файлы: `api/hh_oauth.py`, `services/hh_import.py`, `api/routers/jobs.py`, `docker-compose.override.yml`, тесты `tests/test_hh_oauth.py` и `tests/test_hh_import.py`.

## Google Sheets на 2026-10-08

У каждого подключённого владельца используется один workbook: `Все лиды` для очереди и `Выгрузка` для Telegram-результатов с колонками `Телефон`, `Юзернейм ТГ`, `Дата онлайна`. Удалённые дополнительные листы сначала архивируются в gzip JSON в `/root/TrafficHub/data/runtime/backups/legacy-processed-tabs/`; отдельные старые workbook ID не удаляются. После полного цикла запускается owner-scoped фоновый Check-All, только если владелец сохранил API credentials. Запрос к платному API в рамках release-smoke не запускался.

Проверка 2026-10-08: 4 профиля с настроенным workbook мигрированы и сверены по двум именам листов и заголовкам; 2 профиля без основной таблицы пропущены. Runtime `autolead_bot` и `worker` healthy, локальный и публичный `/api/health` — 200, maintenance off. Изменение в server repo: commits `d90f71551fc3bf5ae7ca4c45945a01410021b8bd`, `d2155357768276e757c8830caca13e45fcdf1c09`. Evidence: `C:/Users/admin/Desktop/Project/outputs/traffichub-sheets-single-book-20261008/EVIDENCE.md`.
