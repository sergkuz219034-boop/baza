# Database

Теги: #архитектура

## Data planes

### `autolead.db`

Источник: `remote_server_snapshot/utils/database.py`

Таблицы:

- `leads`
- `send_history`
- `invite_history`
- `invite_message_state`
- `retry_queue`
- `run_log`
- `autofit_seen`
- `control_sync_queue`

### `control.db`

Источник: `remote_files/utils/control_store.py`

Таблицы:

- `license_users`
- `app_configs`
- `user_app_configs`
- `app_auth`
- `user_app_auth`
- `campaign_history`

### `traffic_dashboard.db`

Источник: `remote_files/traffic_hub/models/database.py`

Сущности:

- `users`
- `leads`
- `messenger_accounts`
- `tool_run_sessions`
- `funnels`
- `offers`
- `network_integrations`
- `conversions`
- `network_offer_stats`
- `postback_logs`
- `payouts`
- `financial_records`

### `accounts.db`

Источник: `remote_server_snapshot/AccountManager/api/main.py`

Подтверждено только наличие отдельной БД и runtime schema patching.

## Почему БД несколько

- runtime-state и бизнес-сущности живут в разных контурах;
- control plane отделён от рабочего цикла;
- AccountManager специально изолирован.

## Смежные страницы

- [[Multi-Tenant]]
- [[Infrastructure]]
