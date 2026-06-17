# Leads service

Теги: #сущность

## Тип

Сервис

## Где находится

`remote_server_snapshot/services/leads_service.py`

## Роль в системе

Содержит основную бизнес-логику operational цикла: загрузка конфига, сбор лидов, загрузка в Sheets, рассылка, retry queue, SuperJob и планировщик.
Фактический live-helper для Sheets сейчас `upload_to_sheets`; старый `upload_resumes_to_sheets` в runtime отсутствует и не должен использоваться.

## Входы

- user config
- Rabota.ru tokens
- Google Sheets credentials
- локальная runtime БД

## Выходы

- новые лиды
- записи в `autolead.db`
- обновления Sheets
- send/retry статистика

## Зависимости

- [[Runtime database]]
- [[Control store]]

## Типовые сбои или риски

- конфиг drift;
- сложные fallback-ветки;
- shared lock `_cycle_running`.
- несовместимость между сервисным слоем и helper API Sheets при отставании server runtime от кода;
- stale job state после падения фазы, если не сбрасывать owner-scoped queue state отдельно от логов.
