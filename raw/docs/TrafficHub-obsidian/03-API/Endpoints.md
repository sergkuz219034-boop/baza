# Эндпоинты API

## Leads (`api/routers/leads.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/leads` | Список лидов (пагинация, фильтр, поиск) |
| GET | `/api/leads/export` | CSV экспорт |
| POST | `/api/leads/resend` | Переотправка лида |

## Jobs (`api/routers/jobs.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/jobs/run` | Запуск задачи (autolead/upload/send/full-cycle/superjob) |
| POST | `/api/jobs/stop` | Остановка задачи |
| GET | `/api/jobs/status` | Статус текущей задачи |

## Settings (`api/routers/settings.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/settings` | Чтение конфига |
| POST | `/api/settings` | Запись конфига |
| POST | `/api/settings/import` | Импорт бандла |
| GET | `/api/settings/export` | Экспорт бандла |
| POST | `/api/settings/google-sa` | Загрузка service_account.json |
| POST | `/api/settings/rabota-token` | OAuth token flow |
| POST | `/api/settings/clear-db` | Очистка БД |

## Offers (`api/routers/offers.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/offers` | Список offers |
| POST | `/api/offers` | Добавить offer |
| PUT | `/api/offers/{id}` | Обновить offer |
| DELETE | `/api/offers/{id}` | Удалить offer |
| POST | `/api/offers/import` | Импорт JSON |
| GET | `/api/offers/export` | Экспорт JSON |

## Stats (`api/routers/stats.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/stats/summary` | KPI summary |
| GET | `/api/stats/history` | Данные для графиков |

## Avito (`api/routers/avito.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/avito/import` | Импорт Avito CSV/XLSX |

## System (`api/routers/system.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Health check |

## Control (`api/routers/control.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/control/health` | Health control store |

## Debug (`api/routers/debug.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/debug/*` | Диагностика |
