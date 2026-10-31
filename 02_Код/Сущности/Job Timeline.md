# Job Timeline

## Что это
Persistent append-only журнал событий job поверх текущего Redis/job state.

## Таблица
`autolead_job_events`

Ключевые поля:
- `owner_username`
- `job_id`
- `command`
- `event_type`
- `status`
- `ts`
- `progress_json`
- `message`
- `error`
- `payload_json`

## Endpoint
`GET /api/jobs/timeline?limit=&job_id=`

Дополнительно для admin:

`GET /api/jobs/timeline?owner=artem&limit=30`

## Ownership
Обычный пользователь видит только свои job-события, даже если передаст `owner` другого пользователя. Admin может передать `owner` явно и смотреть timeline нужного профиля.

## UI
В `Admin панель` есть admin-only карточка `Диагностика runtime`, внутри неё блок `История задач`:

- пустой owner = текущий пользователь;
- заполненный owner работает только для admin;
- выводятся последние события, статус, команда, сообщение и ошибка.

## Почему не только Redis
Redis хранит быстрый текущий state. Для расследования зависших и завершённых job нужна persistent история после refresh/restart API.

## Связанные файлы
- `/root/TrafficHub/traffic_hub/services/job_queue.py`
- `/root/TrafficHub/utils/runtime_store_pg_jobs.py`
- `/root/TrafficHub/utils/database.py`
- `/root/TrafficHub/api/routers/jobs.py`
- `/root/TrafficHub/dashboard/index.html`
- `/root/TrafficHub/dashboard/app.js`

## Связанные заметки
- [[Runtime database]]
- [[Runtime Inspector]]

## 2026-10-09 — нулевой прогресс команды upload во время HH импорта

Подтверждено runtime: admin upload running с 21:12:08, progress total/processed/forms_total равны 0, detail пустой. job_runner.py ветка upload после run_scraper запускает import_hh_leads, но reset_progress только обнуляет счётчики; этапы upload не публикуются. Лог worker 21:15:58 подтверждает append 59 rows, поэтому нулевая панель не доказывает зависание. UI renderJobProgress показывает fallback «Выполняется · ожидаем данные о прогрессе» при отсутствии total. Нужна передача реальных этапов/счётчиков, а не выдуманный процент. Активная задача не останавливалась, production-правка по этому расследованию пока не выпущена. Evidence: C:/Users/admin/Desktop/Project/outputs/progress-upload-20261009/status.log, logs.log, finally.log.

## 2026-10-09 — учёт отправки в Check-All и закраска

Выпущен server commit dcb52f0b696bbed33617c64775f6384990d36e9b: веб-приложение healthy, /api/health 200. services/checkall_jobs.py закрашивает только номера партии с подтверждённым provider_id; отклонённые до принятия заявки вновь доступны для проверки, uncertain/submitting зарезервированы без закраски. Результат сохраняется в «Выгрузка», строго A:C: Телефон / Юзернейм ТГ / Дата онлайна. Settings кнопка теперь явно названа «Проверить непрочеканные номера», лимит 1–100, операция платная по тарифу провайдера. Общая проверка и HH daily используют общий helper выделения принятых номеров. Воркер пока на предыдущем image: обновление без прерывания jobs ожидает idle, script /home/codex/progress-upload-20261009/deploy-when-idle.sh, актуальный target dcb52f0b6.

По Excel пользователя HH_admin_completed_collection_2026_10_05_837_unique_Telegram_Act.xlsx подтверждены 531 уникальный результат (имя файла 837 не является числом строк). Результаты зарегистрированы owner=admin как verified_manual_result с SHA256 источника; платный POST не выполнялся. Эти номера закрашены в совпадающих строках. У партии 574 номеров, отклонённой Check-All HTTP400 без provider_id, снят старый голубой фон в 978 строках двух листов; другие цвета не менялись. Backup форматов: /app/data/runtime/check-highlight-backups-20261009. Evidence: C:/Users/admin/Desktop/Project/outputs/progress-upload-20261009/highlight-reconcile.log, highlight-release.log, highlight-check2.log. 2 целевых теста закраски/резервирования passed; ранее 44 теста этапов и связанных зависимостей passed. Отправка новой платной проверки и реальный ответ провайдера не запускались.

### Сверка пользовательских пачек с общей базой — 2026-10-10
Read-only сверены13xlsx/xlsm из C:/Users/admin/Desktop/проверка по нормализованным телефонам со свежими листами admin «Все лиды»/«Выгрузка». Дата отклика сравнивается с датой в имени пачки; отсутствие даты не означает свежий отклик. В hh06.10:445/447 найдено,200 с датой раньше06.10; две сотни пользователя точно строки249–348 и349–448 этой пачки. Результаты не доказывают дату отправки на чек или ошибку импорта. Строки не окрашивались, данные не менялись. Evidence C:/Users/admin/Desktop/Project/outputs/phone-batches-20261010/folder-old-dates-summary.json; source-batches-summary.json. Деталь с телефонами хранится только в локальном outputs, не вwiki.

### 2026-10-10 — Дополнение выгрузки из файлов проверок
По прямому запросу пользователя сверены новый файл Отклики_10-10-2026.xlsx и 13 файлов проверок. В admin «Выгрузка» добавлено 3831 отсутствующих строк, обновлено 246 строк, заполнено 235 пустых юзернеймов; новые строки содержат 2781 юзернейм. Непустые прежние поля сохранены. Запись выполнена через канонический serializer pending; повторное чтение подтвердило новые строки и сохранность всех старых значений кроме согласованных пустых B:C. Файлы только с телефонами не объявлены подтверждёнными проверками; подсветка не менялась. Отдельный файл без дублей содержит 140 кандидатов: исключены 9 внутренних повторов и 32 номера из обоих листов общей базы. Доказательства: C:/Users/admin/Desktop/Project/outputs/import-checks-20261010/verification.json; before-and-plan.json (приватные данные, не копировать в wiki); clean-data.json. Итоговый размер выгрузки 10857 строк без заголовка.

