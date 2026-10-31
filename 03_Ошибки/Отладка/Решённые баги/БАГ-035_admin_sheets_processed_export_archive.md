# БАГ-035: admin Sheets export не заполнял архив закрытых строк

## Симптом

- У `admin` основная Google Sheets таблица содержала тысячи строк со статусами `Нет номера`, `Нет оффера`, `Суточный лимит`, но отработанная таблица почти не росла.
- Пользовательский симптом: "не заполняется отработанная таблица на экспорт".

## Зона системы

- `modules/sheets_sync.py`
- `services/leads_service.py::run_full_cycle()`
- Google Sheets admin:
  - основная: `RabotaRu_Leads_Pending`
  - отработанная: `RabotaRu_Leads_Export`

## Гипотеза

- Export заполняется только для успешных terminal-результатов, а большинство закрытых строк остаётся только в основной таблице со статусом.

## Проверка

- Runtime под `bind_current_username("admin")`.
- До чистки в основной таблице было 18398 рабочих строк, из них 18321 строка с непустым `Статус`.
- Основные статусы закрытых строк:
  - `Нет номера`: 8390
  - `Нет оффера`: 4961
  - `Суточный лимит`: 3523
  - `Отправлено`: 555
  - `Дубль`: 342
- Код до фикса:
  - `append_processed_leads()` фильтровал только `is_campaign_result_processed()`;
  - `is_campaign_result_processed()` принимал только `sent`, `duplicate`, `already_sent`, `invited`, `already_invited`, `offer_disabled`;
  - `no_phone`, `no_offer`, `daily_limit`, `error` только помечались в основной таблице через `mark_pending_leads_processed()`.

## Наблюдение

- Отработанная таблица имела старый короткий header без `Резюме`, `Статус`, `Дата отработки`, `Офферы`.
- Дополнительный дефект: `get_processed_contact_keys()` при чтении отработанной таблицы вызывал `_ensure_headers(..., settings.EXPORT_FIELDS)` и мог снова портить header export.

## Вывод

- Google Sheets API работал корректно; причина была в контракте TrafficHub.
- Отработанная таблица фактически была "успешно обработанные", а не "все закрытые/отработанные".
- Для операционной очереди корректнее: основная таблица хранит только blank-status очередь, отработанная таблица хранит все закрытые результаты с причиной закрытия.

## Исправление

- Product commits:
  - `0e40d05c2` — `append_processed_leads()` архивирует все markable результаты и пишет полный export header.
  - `7e94da15f` — `get_processed_contact_keys()` использует тот же полный export header и больше не портит первую строку.
- Тесты:
  - `tests/test_sheets_queues.py`
  - `tests/test_leads_service_sheets_flow.py`
- Live deploy: `autolead_bot` и `worker` пересобраны и healthy.
- GitHub checks для `7e94da15f`: CI success, Docker build success.

## Чистка admin Google Sheets

- Перед чисткой включался maintenance mode для `admin`; после проверки выключен.
- Worker останавливался на время массовой перестройки строк.
- Backup до изменения:
  - container: `/app/data/runtime/backups/admin_sheets_cleanup_apply_20260630_215718`
  - host copy: `/home/codex/traffichub_runtime_backups/admin_sheets_cleanup_apply_20260630_215718`
- После чистки:
  - основная таблица: 70 строк, все со blank `Статус`;
  - `load_pending_leads_for_send()`: 70 строк;
  - отработанная таблица: 12569 строк;
  - processed contact keys: 18260;
  - обе таблицы имеют единый header:
    `Фио`, `Пол`, `Вакансия`, `Дата`, `Номер`, `Почта`, `Резюме`, `Город`, `Возраст`, `ДатаРождения`, `Статус`, `Дата отработки`, `Офферы`.

## Актуализация контракта — 2026-10-08

Этот баг фиксировал прежнюю двухтабличную схему и был верным для того релиза. По новому продуктовому контракту отдельная архивная таблица закрытых результатов больше не используется: один workbook содержит `Все лиды` и `Выгрузка` для Check-All. Статусы закрытия остаются на `Все лиды`; автоматическая проверка Telegram после полного цикла пишет телефон, username и дату онлайна в `Выгрузка`. Лишние листы удаляются только после gzip JSON backup.

Для 4 настроенных workbook production-проверка подтвердила по два листа; два профиля без main workbook не мигрировались. История миграции и ограничения: `C:/Users/admin/Desktop/Project/outputs/traffichub-sheets-single-book-20261008/EVIDENCE.md`.


### Подсветка чеков при следующей выгрузке — 2026-10-10

По уточнению пользователя подсвечиваются только действительно отправленные на чек номера, а не диапазон до кандидата. `modules/sheets_sync.py::_append_rows_to_end` очищает только backgroundColor/backgroundColorStyle точного updatedRange, подтверждённого append_rows; прежние строки и остальные атрибуты форматирования не затрагивает. Число строк диапазона сверяется с добавленной партией. Это исключает наследование голубой подсветки последней строки новыми непрочеканными строками. Нативная сортировка продолжает перемещать строки вместе с форматами. Журнал подтверждённых provider_id/verified_manual_result используется для восстановления подсветки; ambiguous/reserved номера не считать принятыми. Локальная целевая проверка exact-range, single append, empty batch PASS. Доказательства: `C:/Users/admin/Desktop/Project/outputs/check-highlight-20261010/{test.py,release.log}`. Live массовая выгрузка ради проверки не запускалась.


### Сбор HH.ru / Работа.ру и удаление Зарплата.ру — проверено 2026-10-10

Пользователь видел нулевой счётчик HH.ru и не видел сбор Работа.ру. Runtime подтвердил: токен admin существовал в origin, но RU RabotaRuClient в owner-context пытался загрузить cloud auth без PostgreSQL и отказывался от leased tmpfs-файла. Исправлено через ContextVar с точной парой owner/path: чужой owner не получает токен, контекст сбрасывается, refresh возвращается через подписанную lease, общий file-fallback в user-context не добавлен. Отсутствие токена в rabota_collect теперь ошибка, а не ложный успешный пустой сбор.

HH.ru пропускает только counters.total с числовым int=0 (не bool/строка/неизвестное значение); неизвестные счётчики обходит как прежде. Первый новый контакт сохраняется сразу, следующие — прежними партиями. Progress показывает vacancies_done/vacancies_total и отдельно реально сохранённые лиды; частота API не увеличена, лимиты/дедупликация сохранены. Перед leased сбором Работа.ру публикуется отдельный этап rabota. Сортировка/подсветка прежних строк не менялись.

По прямому указанию пользователя Зарплата.ру убрана из source_states, её запуск заблокирован для всех владельцев даже при старом enabled=true; старый route ведёт на Источники, вкладка скрыта, loader вакансий не обращается к API. Исторические лиды, конфигурации и credentials не удалены.

Целевые проверки: 50 tests PASS (lease credentials admin/ordinary-owner, mismatch/refresh/context cleanup, HH collections/dedupe/rate-limit, owner progress, retired source, durable delivery); browser fixture dark/light 1440/390 — реальные progress counters/Работа.ру stage/no horizontal overflow PASS. Live RU read-only вакансии: HTTP200, 2 вакансии, 1.0s. Проверочный owner job 7dda173b290e472abf87675985f573b9 command=upload: rabota_collect completed/ok=true/363 полученных лида; HH сохранено3 новых, 2/2 вакансии; job завершился idle без ошибки. 363 — число полученных лидов ДО дедупликации, не обещание363 новых строк.

Product commits: 749152c6c (leased token + HH ускорение); 4ae8213d7 (Работа.ру stage + удаление Зарплата.ру). Доказательства: C:/Users/admin/Desktop/Project/outputs/collection-speed-20261010/{credentials-flow.log,ru-runtime.log,token.log,rabota-smoke.log,ru-progress.log,verify-status.log,test-pg.log,browser.log,release.log,release-final.log,final-health.log}. Rollback images /home/codex/collection-speed-20261010/rollback-images; RU остановленный rollback container и приватный rollback-inspect.json сохранены. Реальные аккаунты других владельцев не использовались для отправок: обычный пользователь проверен изолированными тестами, не массовой production-рассылкой.
