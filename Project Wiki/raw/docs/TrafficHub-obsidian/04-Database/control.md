# control.db

Файл: `utils/control_store.py` (316 строк)

## Таблицы

### license_users
```sql
CREATE TABLE license_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT UNIQUE,
    hwid TEXT,
    role TEXT DEFAULT 'operator',
    password_hash TEXT,
    salt TEXT,
    license_key TEXT,
    expires_at TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT,
    updated_at TEXT
);
```

### app_configs
```sql
CREATE TABLE app_configs (
    key TEXT PRIMARY KEY,
    value TEXT,           -- JSON
    updated_at TEXT
);
```

### app_auth
```sql
CREATE TABLE app_auth (
    key TEXT PRIMARY KEY,  -- 'google_sa' | 'rabota_tokens'
    value TEXT,            -- base64 или JSON
    updated_at TEXT
);
```

### campaign_history
```sql
CREATE TABLE campaign_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT,
    action TEXT,
    details TEXT,
    created_at TEXT
);
```

## Связанное

- [[05-Configuration/License|Лицензирование]]
- [[03-API/Auth|Авторизация]]
- [[04-Database/Schema|Схема БД]]
