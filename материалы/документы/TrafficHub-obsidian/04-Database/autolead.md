# autolead.db

Файл: `utils/database.py` (865 строк)

## Таблицы

### leads
```sql
CREATE TABLE leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    email TEXT,
    vacancy TEXT,
    city TEXT,
    gender TEXT,
    age INTEGER,
    source TEXT,
    status TEXT,
    score INTEGER,
    raw_data TEXT,        -- JSON
    partner TEXT,
    created_at TEXT,      -- ISO 8601 MSK
    updated_at TEXT
);
```

### send_history
```sql
CREATE TABLE send_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    offer_name TEXT,
    platform TEXT,
    status TEXT,
    response TEXT,
    error TEXT,
    screenshot_path TEXT,
    created_at TEXT,
    FOREIGN KEY (lead_id) REFERENCES leads(id)
);
```

### invite_history
```sql
CREATE TABLE invite_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    status TEXT,
    response TEXT,
    created_at TEXT,
    FOREIGN KEY (lead_id) REFERENCES leads(id)
);
```

### retry_queue
```sql
CREATE TABLE retry_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_data TEXT,       -- JSON полный
    offer_name TEXT,
    attempt INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    next_attempt_at TEXT,
    error TEXT,
    created_at TEXT
);
```

### run_log
```sql
CREATE TABLE run_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT,
    status TEXT,
    leads_found INTEGER,
    leads_sent INTEGER,
    errors INTEGER,
    started_at TEXT,
    finished_at TEXT
);
```

### autofit_seen
```sql
CREATE TABLE autofit_seen (
    resume_id TEXT PRIMARY KEY,
    seen_at TEXT
);
```

### control_sync_queue
Внутренняя таблица для синхронизации с control.db.

## Связанное

- [[материалы/документы/TrafficHub-obsidian/01-Architecture/DataFlow|Data Flow]]
- [[материалы/документы/TrafficHub-obsidian/01-Architecture/Scoring|Скоринг]]
