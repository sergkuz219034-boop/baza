# БАГ-018: Content Bot дублировал targets/tasks и штормил refresh

Статус: решено  
Дата: 2026-06-19  
Зона: `/root/TrafficHub/AccountManager/api/routers/content.py`, `/root/TrafficHub/AccountManager/services/content_bot_service.py`, `/root/TrafficHub/AccountManager/dashboard/index.html`, `/root/TrafficHub/AccountManager/dashboard/app.js`, `traffichub_account_manager`

## Симптом

- `content bot` и content-dashboard были доведены до нелогичного состояния после несогласованных правок другой моделью.
- UI скрывал список posting targets, поэтому live мог хранить дубли и smoke-target'ы без явной визуализации.
- backend позволял повторно создавать:
  - одинаковые `PostingTarget`;
  - одинаковые open `PostingTask` для одного `content_item_id + target_id`.
- dashboard делал repeated bursts `GET /api/content/*`, что выглядело как дублирование меню/состояния и лишний refresh storm.

## Проверка

- На live-хосте `150.241.70.31` подтверждён канонический repo `/root/TrafficHub`.
- В `docker compose ps` подтверждён активный контейнер `traffichub_account_manager`.
- В live checkout найдены реальные точки `content bot`:
  - `AccountManager/api/routers/content.py`
  - `AccountManager/services/content_bot_service.py`
  - `AccountManager/dashboard/index.html`
  - `AccountManager/dashboard/app.js`
- В live DB на момент расследования было:
  - `PostingTarget #1 = CadryPro Official`
  - `PostingTarget #2 = Content Bot Smoke Admin`
  - `content_bot_default_target_id = 1`
  - единственная историческая smoke-task была `posted` в target `2`
- В логах `AccountManager/data/logs/account_manager.log.2026-06-18` подтверждены пачки повторяющихся `GET /api/content/*`.
- Причина refresh storm подтверждена кодом:
  - `window.refreshDashboardSummary = refreshAll`
  - `TelegramModule.reload()`, `GoogleModule.reload()`, `SocialModule.reload()` вызывали `window.refreshDashboardSummary?.()`
  - это повторно запускало весь `refreshAll()` вместо узкого summary-refresh.
- Причина дублей подтверждена кодом:
  - `create_target()` создавал новую запись без поиска по `username/telegram_id`
  - `approve_item()` и `create_task()` не переиспользовали existing open task
  - `save_bot_config()` не умел канонически переключать `default_target_id` на existing target
  - `ensure_default_target()` искал target в первую очередь по `title`, что позволяло рассинхрон между channel identity и default target.

## Решение

- В backend добавлена idempotency-логика:
  - нормализация channel identity (`@username` vs raw username vs numeric chat id)
  - переиспользование existing `ContentSource` и `PostingTarget`
  - переиспользование existing open `PostingTask` для одного `content_item_id + target_id`
  - валидация `random_delay_min_sec <= random_delay_max_sec`
- В `content_bot_service.save_bot_config()` добавлена поддержка `default_target_id`:
  - выбранный target становится каноническим default target;
  - `content_bot_target_channel`, `content_bot_target_title` и `content_bot_default_target_id` синхронизируются из существующего target.
- В `ensure_default_target()` приоритет смещён на `telegram_id/username`, а не только на `title`.
- В dashboard исправлен refresh-контур:
  - `window.refreshDashboardSummary` больше не алиас на `refreshAll()`;
  - summary-refresh теперь отдельный и не вызывает full reload всего content/API UI.
- В dashboard добавлены недостающие live-controls:
  - таблица posting targets;
  - явное отображение default target;
  - кнопка `По умолчанию` для target;
  - кнопка удаления target;
  - отдельная card для `Content Bot` config/status;
  - более логичные action-кнопки для content items и posting tasks.

## Проверка после фикса

- Выполнен rebuild/recreate:
  - `docker compose build account_manager`
  - `docker compose up -d --force-recreate account_manager`
- Подтверждено, что `traffichub_account_manager` поднят на новом image и healthy.
- Внутри обновлённого контейнера выполнен targeted verification script:
  - duplicate target с одинаковым channel identity больше не создаётся;
  - duplicate open posting task для одного content item и target больше не создаётся;
  - `save_bot_config(default_target_id=...)` синхронизирует bot config с выбранным target.
- Результат verification: `content-bot verification passed`.

## Вывод

Проблема была не в одном “кривом меню”, а в двух независимых дефектах:

- frontend refresh storm создавал ощущение дублирования и нестабильного UI;
- backend не имел idempotent guard'ов и позволял плодить скрытые дубли targets/tasks.

Теперь `content bot` снова имеет один логический контур:

- target можно видеть и явно выбирать как default;
- повторное действие не плодит новый open task без необходимости;
- bot config и default target синхронизируются через один канонический path;
- UI больше не запускает full refresh по цепочке из summary callbacks.
