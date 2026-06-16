# 2026-06-16 Внешний sync с GitHub репозиторием baza восстановлен

## Симптом

- ранее sync с `sergkuz219034-boop/baza` фиксировался как заблокированный;
- пользователь дал новый GitHub token и запросил синхронизировать wiki с реальным repo.

## Зона системы

- внешняя knowledge base `baza`;
- локальная wiki;
- GitHub access path.

## Гипотеза

Предыдущая блокировка была не в отсутствии репозитория, а в невалидном или недостаточном access path/token для GitHub clone.

## Проверка

Подтверждено локально `2026-06-16`:

- `GET https://api.github.com/user` новым токеном -> `200`
- login -> `sergkuz219034-boop`
- `GET https://api.github.com/repos/sergkuz219034-boop/baza` -> `200`
- `GET https://api.github.com/search/repositories?q=baza+user:sergkuz219034-boop` -> `200`, найден `sergkuz219034-boop/baza`
- `git clone https://sergkuz219034-boop:<token>@github.com/sergkuz219034-boop/baza.git` -> успешно

## Наблюдение

- репозиторий `baza` существует и доступен;
- локальная папка `wiki/Baza-obsidian` до этого не соответствовала живому дереву repo;
- после клона обновлён реальный раздел `01 Проекты/ТрафикХаб`:
  - server repo
  - SSH access
  - контейнеры
  - ownership/Google Sheets
  - worker/realtime

## Вывод

- источник истины по формату `baza` снова подтверждён;
- локальный mirror `wiki/Baza-obsidian` надо считать синхронизированным с GitHub repo по состоянию на `2026-06-16`;
- старая заметка про `404` стала исторической и больше не описывает актуальное состояние.

## Следующий шаг

- держать `TrafficHub-obsidian` как полную инженерную карту;
- держать `baza` как более краткий внешний слой проекта;
- при следующих изменениях сначала обновлять локальную техническую wiki, потом краткий проектный слой в `baza`.
