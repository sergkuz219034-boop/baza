# Wave-by-wave validation checklist

Дата: 2026-06-01

Связанные документы:
- [2026-06-01 implementation roadmap by waves.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20implementation%20roadmap%20by%20waves.md)
- [2026-06-01 root cause matrix current state.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20root%20cause%20matrix%20current%20state.md)
- [2026-06-01 patch-plan config save ownership split.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20config%20save%20ownership%20split.md)
- [2026-06-01 patch-plan offer mapping drift.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20offer%20mapping%20drift.md)
- [2026-06-01 patch-plan run status and retry queue.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20patch-plan%20run%20status%20and%20retry%20queue.md)
- [2026-06-01 server-side ssh and proxy hardening plan.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20server-side%20ssh%20and%20proxy%20hardening%20plan.md)
- [2026-06-01 wave 1 execution pack security hardening.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%201%20execution%20pack%20security%20hardening.md)
- [2026-06-01 wave 2 execution pack config ownership split.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%202%20execution%20pack%20config%20ownership%20split.md)
- [2026-06-01 wave 3 execution pack offer mapping merge correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%203%20execution%20pack%20offer%20mapping%20merge%20correction.md)
- [2026-06-01 wave 4 execution pack run status truthfulness.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%204%20execution%20pack%20run%20status%20truthfulness.md)
- [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)
- [2026-06-01 consolidated runtime patch bundle.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20runtime%20patch%20bundle.md)

## Анализ

Это короткий операторский checklist по волнам.

Использование:
- после завершения каждой волны пройти пункты сверху вниз
- если любой пункт не проходит, не переходить к следующей волне

## Волна 0. Подготовка

Проверить:

1. Работа идёт от текущего `remote_server_snapshot`, а не от старых diff.
2. Есть backup:
- конфигов
- compose/env
- БД/state
3. Есть подтверждённый админский доступ.
4. Понятен rollback-путь.

Стоп-сигналы:
- нет резервного доступа
- rollback не определён

## Волна 1. Security hardening

Проверить:

1. Новый SSH-доступ по ключу реально работает в отдельной сессии.
2. После hardening:
- `PasswordAuthentication no`
- `PermitRootLogin prohibit-password` или `no`
3. Публичные домены отвечают.
4. Auth/perimeter secrets после ротации работают.
5. Если `ACCOUNT_MANAGER_BASIC_AUTH_*` оставлены:
- они реально применяются
  или
- явно признаны legacy и удалены

Стоп-сигналы:
- вход по ключу не подтверждён
- после изменения SSH policy доступ не проверен новой сессией
- auth/perimeter flow даёт `401/403` без ожидания этого

## Волна 2. Config ownership split

Проверить:

1. Обычный user save обновляет:
- user profile
- local config
2. Обычный user save не меняет shared HWID-config.
3. Явный shared-save путь всё ещё существует там, где он нужен.
4. Старый тестовый контракт обновлён.

Стоп-сигналы:
- user edit по-прежнему меняет shared config
- shared-save больше нигде не доступен, хотя нужен миграциям/админам

## Волна 3. Config merge correction

Проверить:

1. Пустой `offer_mapping` в existing profile больше не убивает shared offers без явного решения.
2. Непустой `offer_mapping` пользователя по-прежнему может переопределять shared mapping.
3. Добавлен regression-тест на drift existing profile.
4. Задокументирована семантика:
- `[]` = наследовать
  или
- `[]` = явно отключить

Стоп-сигналы:
- поведение пустого списка осталось не определено
- regression-теста нет

## Волна 4. Run status truthfulness

Проверить:

1. Timeout Sheets больше не закрывает run как `ok`.
2. Успешный run с `0` добавленных строк без ошибки всё ещё `ok`.
3. `run_log.status` корректно читается UI/отчётами.
4. Новые статусы не ломают текущие consumers.

Стоп-сигналы:
- любые старые consumers падают на новых статусах
- ошибка фазы всё ещё маскируется как обычный `0`

## Волна 5. Retry lifecycle correction

Проверить:

1. Terminal `missing_offer_mapping` больше не крутится бесконечно.
2. Временные retryable ошибки по-прежнему ретраятся.
3. В логах различимы:
- `terminal`
- `retryable_error`
- `duplicate`
- `skipped`
4. Retry queue не раздувается старыми terminal items.
5. Retry lead перед отправкой содержит vacancy context, если он есть в `leads`:
- `Вакансия`
- `Дата`
- `_raw_data.vacancy_id`
6. Incident `нет оффера для vacancy_id: ... ()` не воспроизводится для уже замапленных `vacancy_id`.

Стоп-сигналы:
- временные ошибки начали удаляться как terminal
- terminal items всё ещё возвращаются в каждом цикле
- enrichment начал подставлять нерелевантный vacancy context массово

## Волна 6. Integration verification and cleanup

Проверить:

1. WS job-status доходит end-to-end.
2. Historical patch-plans не противоречат текущему snapshot.
3. Основные UI/API сценарии живы.
4. Investigations и solution-notes синхронизированы по active vs historical.

Стоп-сигналы:
- документы снова расходятся с текущим кодом
- WS status остаётся недоказанным, но считается “закрытым”

## Быстрый итог

Переходить к следующей волне можно только если:

1. Нет stop-сигналов в текущей волне.
2. Пройдены обязательные проверки.
3. Не осталось неразрешённой ownership-неопределённости, влияющей на следующую волну.
