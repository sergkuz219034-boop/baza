# 2026-07-18 полный аудит TrafficHub

Теги: #debug #архитектура

## Симптом

Требуется проверить весь проект на ошибки от критических до простых, включая код, конфигурацию, тесты, deployment и live-runtime.

## Зона проекта

- Live source repo: `/root/TrafficHub`
- Локальный workspace: wiki и SSH-инструменты, не source repo
- Связанные сущности: [[TrafficHub app]], [[Runtime database]], [[Runtime logging]], [[Remote ops tools]]

## Текущая гипотеза

В проекте могут одновременно присутствовать функциональные дефекты, security-риски, ошибки tenant isolation, deployment drift и простой технический долг; критичность требует подтверждения кодом, тестами или runtime.

## Проверки

### Проверка 1 — границы аудита

- Что сделал: проверил структуру локального workspace и документацию о каноническом source repo.
- Что ожидал: найти локальное зеркало приложения.
- Что увидел: локально доступны wiki и operational SSH tooling; канонический код находится в `/root/TrafficHub` на live-сервере.

### Проверка 2 — source и runtime drift

- Что сделал: проверил `HEAD`, `git status`, container images и health.
- Что ожидал: clean worktree и совпадающий deploy marker.
- Что увидел: `HEAD=17bb3167f33d5314daa227a4ad0f49b00d462506`, 30 modified и 8 untracked файлов; app/worker используют image `traffichub-runtime:75bb44c9fd2b324b57683b7f65537baa743458e1`. Все 10 контейнеров running, 9 health-checkable контейнеров healthy, restart=0, OOM=false.

### Проверка 3 — синтаксис и тесты

- Что сделал: снял локальный clone `HEAD`, наложил 38 live-файлов, проверил Python compileall и 14 JavaScript-файлов через `node --check`; pytest запущен в одноразовом контейнере с отдельным PostgreSQL и без внешней сети.
- Что ожидал: чистый syntax/test gate.
- Что увидел: синтаксических ошибок нет. Полный прогон: 618 passed, 43 skipped, 8 failed. После устранения read-only артефактов подтверждено 5 падений.

### Проверка 4 — live-логи

- Что сделал: проверил container state и ошибки за 24 часа.
- Что ожидал: отсутствие повторяемых product errors.
- Что увидел: Lovko partner sync для `admin` повторно не проходит форму авторизации; AccountManager фиксирует `AuthKeyDuplicatedError`, pending asyncio tasks и `GeneratorExit`. Ошибки operator nginx по случайным asset paths похожи на scanner noise, а не product regression.

## Наблюдения

- Факт: локальный workspace не является Git-репозиторием приложения.
- Факт: дальнейшая проверка кода и runtime должна выполняться read-only на live-сервере.
- P1: live source/runtime не имеют воспроизводимой единой ревизии — worktree содержит 38 незакоммиченных файлов, а контейнеры собраны из image marker другой ревизии. `.orig`-файлы лежат рядом с source.
- P1: Telethon session используется с двух IP и уже инвалидирована (`AuthKeyDuplicatedError`); AccountManager дополнительно теряет pending asyncio tasks при teardown/reconnect.
- P1: Lovko sync стабильно падает примерно раз в час: login form остаётся на странице авторизации после submit.
- P2: `api/authz.py::_request_host` без защиты обращается к `request.headers`; два access-token теста падают после добавления host-role enforcement. Production FastAPI Request имеет headers, поэтому это подтверждённая test/API-contract regression, но не доказанный production outage.
- P2: `docker-compose.yml` нарушает закреплённый тестом fail-closed contract для обязательных production secrets; как минимум `OPENROUTER_API_KEY` не задан через `${NAME:?...}`. Требуется решить, обязательный ли ключ для всего compose или только для AI-контуров, и синхронизировать код с тестом.
- P2: `/operator-host` больше не содержит утверждённые операторские KPI-labels (`Новые кандидаты` и связанные строки); UI и contract test разошлись.
- P3: `_load_log_history_messages` возвращает current log раньше более старого rotated log; хронологический контракт нарушен.
- P3: pytest не герметичен без ручных dummy-переменных `ACCOUNT_MANAGER_ENCRYPTION_KEY`, `BOT_TOKEN`, `TARGET_CHAT_ID`; два модуля создают settings на import.
- P3: 43 теста skipped; причины skip требуют отдельной инвентаризации, поэтому эти контуры нельзя считать покрытыми.
- P3: 69 warnings, включая Pydantic class Config deprecation и `crypt`/Starlette TestClient deprecation.
- Факт: Python compileall и JavaScript syntax checks прошли без ошибок.
- Факт: сервер не находится в outage: контейнеры healthy, restart/OOM не обнаружены, диск 50%, доступная RAM около 1.8 GiB.

## Вывод

Критических P0 с доказанным outage, потерей данных или обходом auth не найдено. Подтверждены три P1 operational/release риска, три P2 функциональных/контрактных дефекта и несколько P3 проблем тестовой гигиены и технического долга. Проверка является широким single-pass аудитом, а не доказательством отсутствия всех дефектов во всех 775 tracked-файлах.

## Следующий шаг

1. Зафиксировать или убрать dirty live changes и привязать image к commit.
2. Устранить двойное использование Telethon session и повторить reconnect-тест.
3. Исправить/диагностировать Lovko login flow.
4. Закрыть пять воспроизводимых pytest failures и сделать test env герметичным.
5. Отдельно разобрать 43 skipped tests и security/tenant isolation глубже.

## Связанные заметки

- [[Remote ops tools]]
- [[01_Правила/Плейбуки/Read-only аудит live-сервера]]
- [[02_Код/Архитектура/Карта контейнеров и модулей]]
