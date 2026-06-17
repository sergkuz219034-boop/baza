# Artem full cycle: upload and send root cause

Дата: 2026-06-02

Связанные документы:
- [2026-06-01 autolead 3 log analysis.md](C:/Users/Арт/Desktop/TrafServer/01%20Расследования/2026-06-01%20autolead%203%20log%20analysis.md)
- [2026-06-01 wave 4 execution pack run status truthfulness.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%204%20execution%20pack%20run%20status%20truthfulness.md)
- [2026-06-01 wave 5 execution pack retry lifecycle correction.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20wave%205%20execution%20pack%20retry%20lifecycle%20correction.md)
- [2026-06-01 consolidated runtime patch bundle.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20runtime%20patch%20bundle.md)

## Анализ

Проверка по состоянию на `2026-06-02` показала, что у аккаунта `Artem` полный цикл ломается не в одной точке, а в двух последовательных фазах.

### Фаза 1. Сбор лидов работает

По логу [autolead (3).log](C:/Users/Арт/Downloads/autolead%20(3).log):

- найдено `21` отклик;
- сохранено `16` лидов;
- цикл доходит до выгрузки и рассылки.

Значит первичный сбор с `Rabota.ru` для этого инцидента не является главным блокером.

### Фаза 2. Выгрузка в Google Sheets фактически падает

Подтверждено логом:

- `2026-06-01 15:00:56 ERROR: Sheets upload error: ... Read timed out`
- после этого цикл пишет:
  - `В Sheets добавлено строк: 0`

Подтверждено кодом:

- [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:535)
  - `upload_sheets()` пишет именно в pending-роль через `spreadsheet_role="pending"`
- [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:549)
  - при успехе вызывается `upload_to_sheets(...)`
- [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:560)
  - при ошибке фаза не поднимает richer failure outcome наверх

Для `Artem` это означает:
- новые 21 лид фактически не попали в pending-таблицу;
- следующая send-phase уже не видит свежий материал для нормальной рассылки.

### Фаза 3. Новые лиды не уходят в send-path после провала Sheets

Подтверждено кодом:

- [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:857)
  - при включённых Sheets `run_full_cycle()` пытается брать лиды для send из `load_pending_leads_for_send(config)`
- [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:865)
  - если pending queue пустая, `all_leads_to_send = []`
- [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:872)
  - fallback на локальную БД работает только когда Sheets выключен

Вывод:
- при `google_sheets.enabled=true` полный цикл у `Artem` зависит от успешной pending-выгрузки;
- если pending-upload не состоялся, send-phase для свежих лидов фактически обнуляется.

### Фаза 4. Вместо свежих лидов крутится старый retry-хвост

Подтверждено логом:

- `pending Sheets queue is empty`
- затем сразу `Повторные попытки: 33`
- далее идут массовые:
  - `нет оффера для vacancy_id: 54244364 ()`
  - `54267737`
  - `54279842`
  - `54279727`

Подтверждено конфигом `Artem`:

- в `control.db -> user_app_configs(login='artem')`
- и в `control.db -> app_configs(hwid='9f03a58b9fd366da')`
- все эти `vacancy_id` уже присутствуют в оффере `Воксис`

Значит для этого инцидента версия “оффер не настроен” не подтверждается.

### Retry-path у `Artem` деградирует на sender boundary

Подтверждено кодом:

- [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:686)
  - `process_retry_queue()` строит `base_offer`
- [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py:720)
  - `retry_lead` содержит только:
    - `Фио`
    - `Номер`
    - `Город`
    - `_source_type`
    - `_raw_data.vacancy_id/response_id/resume_id`
- [database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py:760)
  - обычный backlog lead из `load_leads_for_send()` богаче и содержит:
    - `Вакансия`
    - `Пол`
    - `Дата`
    - `_raw_data.vacancy_id`

Это хорошо согласуется с логом вида:
- `нет оффера для vacancy_id: ... ()`

Пустые скобки выглядят как признак отсутствующего vacancy context/name, а не отсутствующего mapping в конфиге.

### Historical evidence ослабляет гипотезу “Воксис вообще не работает”

В `control.db -> campaign_history` есть исторические успешные отправки по `Воксис`.

Значит:
- оффер как таковой уже работал в системе;
- текущий инцидент сильнее похож на runtime/degraded retry-path, чем на “сломанный оффер навсегда”.

## Причина

### 1. `High`: pending Sheets upload у `Artem` реально падает по timeout

- Описание проблемы:
  - новые лиды собираются, но не попадают в pending-таблицу.
- Первопричина:
  - `upload_sheets()` получает `Read timed out` к `sheets.googleapis.com`.
- Возможные последствия:
  - свежие лиды не участвуют в нормальной send-phase;
  - цикл деградирует к старому retry-хвосту.
- Вероятность:
  - `0.95`

### 2. `High`: full cycle при включённых Sheets не переключается на локальный send backlog после failed/empty pending path

- Описание проблемы:
  - после провала pending-upload send-phase не берёт свежие лиды локально.
- Первопричина:
  - при `google_sheets.enabled=true` код ждёт pending-очередь и при пустом результате выставляет `all_leads_to_send = []`.
- Возможные последствия:
  - “полный цикл” формально доходит до рассылки, но не рассылает свежесобранные лиды.
- Вероятность:
  - `0.90`

### 3. `High`: retry send-path у `Artem` ломается не на config mapping, а на payload/schema boundary

- Описание проблемы:
  - retry queue массово выдаёт `нет оффера для vacancy_id`, хотя mapping существует.
- Первопричина:
  - retry lead восстанавливается в урезанном виде и, вероятно, не даёт sender-у полный vacancy context.
- Возможные последствия:
  - повторные попытки бесконечно шумят;
  - отправка по существующему `Воксис` не происходит.
- Вероятность:
  - `0.80`

### 4. `Low/Medium`: login ambiguity вокруг `Artem` / `artem` / `Artem3000`

- Описание проблемы:
  - в `control.db` одновременно видны `Artem`, `Artem3000` и runtime-нормализация в `artem`.
- Первопричина:
  - разные historical login forms и lower-case binding в [user_context.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/user_context.py:15).
- Возможные последствия:
  - путаница в диагностике и ownership;
  - риск не того user profile в соседних сценариях.
- Почему это не главный root cause здесь:
  - текущий run явно пишет `user config сохранён для artem`;
  - `user_app_configs(login='artem')` существует и содержит нужный mapping.
- Вероятность как incident root cause:
  - `0.15`

## План исправления

Для инцидента `Artem` безопасный порядок такой:

1. Сначала закрыть `Wave 4`:
- честно маркировать failed/partial failed run после timeout Sheets.

2. Затем закрыть `Wave 5A`:
- прекратить бесконечный terminal retry noise.

3. Затем закрыть `Wave 5B`:
- enrich retry lead vacancy context из `leads` table.

4. Отдельно после этого проверить operational-причину самого timeout к Google Sheets:
- сеть
- quota
- latency
- service account access

## Diff

Прод-код на этом шаге не менялся.

Новый incident-level документ:
- [2026-06-02 Artem full cycle upload and send root cause.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-02%20Artem%20full%20cycle%20upload%20and%20send%20root%20cause.md)

Этот вывод опирается на:
- [autolead (3).log](C:/Users/Арт/Downloads/autolead%20(3).log)
- [leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py)
- [database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py)
- `control.db` runtime/config state

## Риски

Если лечить только “нет оффера”:
- останется проваленная pending-выгрузка;
- свежие лиды всё равно не будут доходить до send-phase.

Если лечить только Sheets timeout:
- full cycle начнёт лучше наполнять pending;
- но старый retry-tail всё равно продолжит деградировать на sender boundary.

Если считать проблемой только конфиг `Воксис`:
- будет патчиться не та причина;
- потому что mapping уже подтверждён и в user, и в shared config.

## Проверка после исправления

После будущих правок для `Artem` нужно отдельно проверить:

1. Новый полный цикл:
- timeout Sheets больше не маркируется как `ok`
- новые лиды реально доходят до pending spreadsheet

2. Send-phase:
- при успешной pending-выгрузке новые лиды реально попадают в рассылку

3. Retry-phase:
- `нет оффера для vacancy_id: ... ()` исчезает или резко сокращается для `Воксис`
- terminal retry items не крутятся бесконечно

4. Historical compatibility:
- уже рабочие офферы вроде `Воксис` не деградируют на обычном send-path

## Дополнительные улучшения

Следующий самый полезный шаг для `Artem` уже почти implementation-level:

1. Либо реально внедрять runtime bundle:
- [2026-06-01 consolidated runtime patch bundle.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20runtime%20patch%20bundle.md)

2. Либо дополнительно добрать operational evidence по Google Sheets timeout:
- частота
- воспроизводимость
- доступность spreadsheet/service account

Это позволит отделить:
- кодовую проблему truthfulness/retry,
- от сетевой или quota-проблемы внешнего Google API.
