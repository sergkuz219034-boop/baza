# Legacy статусы, email и пол Autolead

## Симптом

Старые строки Sheets со статусами `Новый`, `Ошибка`, `Отработан`, `Нет оффера`, `Суточный лимит` не доходили до штатной рассылки. Отсутствие email блокировало любой оффер. У части лидов пол оставался пустым.

## Зона системы

- `/root/TrafficHub/modules/sheets_sync.py`
- `/root/TrafficHub/services/backfill_service.py`
- `/root/TrafficHub/services/leads_service.py`
- `/root/TrafficHub/modules/vbiv_bot.py`
- `/root/TrafficHub/utils/data_processor.py`
- `/root/TrafficHub/modules/platforms/base.py`

## Гипотеза

Пустая проверка статуса в Sheets, общий email gate и несколько независимых gender fallback создают повторяющиеся ложные блокировки.

## Проверка

- `load_pending_leads_for_send()` до исправления пропускал каждую строку с непустым `Статус`.
- `backfill_service._has_required_contact_data()` требовал email и резюме до matching оффера.
- `normalize_lead()` и `BasePlatform` оставляли неизвестный пол пустым; `GeneralPlatform` и Lovko угадывали его иначе.

## Наблюдение

Исправление `0b40885f8` добавляет явный bounded job `legacy_repair`, который выбирает только legacy-статусы и вызывает обычный `run_sender(..., respect_period=False)`. Защита конкретного оффера остаётся в owner-scoped send history. Статусы, дата, офферы и пол обновляются штатными writer-ами Sheets и PostgreSQL.

Email нормализуется на границе Sheets/runtime: `нету`, `нет`, `none`, `null`, `-` становятся пустыми. Email обязателен только при capability `requires_email`; compatibility fallback для существующих mapping Тетрики находится в одном helper. Пол: API → ФИО → `муж`.

## Вывод

Нет отдельного упрощённого sender и нет массового `UPDATE status -> new`. Legacy repair запускается явно, с лимитом (по умолчанию 50, максимум 500) через `POST /api/jobs/legacy-repair` и проходит тот же campaign/history contract, что обычный цикл.

## Следующий шаг

После deploy: read-only scan owner-bound Sheets, затем `limit=1` controlled smoke; проверить Sheets, `autolead_leads`, `autolead_send_history`, retry queue. Полный repair запускать только после подтверждения sample.

Связи: [[2026-08-10 Формат отработанной таблицы]], [[2026-08-11 Alex Ozon устаревшие обязательные поля]].
