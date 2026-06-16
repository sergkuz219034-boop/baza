# Схема БД

Проект использует **три изолированных SQLite базы**:

```
autolead.db  ← основные данные (лиды, история)
control.db   ← пользователи, конфиг, лицензии
traffic_dashboard.db  ← CRM данные
```

## Связь

```mermaid
graph TD
    A[autolead.db] -->|sync thread| B[control.db]
    C[traffic_dashboard.db] <-->|SQLAlchemy| D[TrafficHub CRM]
    B <-->|License/Auth| E[main.py]
```

Mermaid-диаграммы схем каждого файла — в соответствующих заметках.

## Связанное

- [[материалы/документы/TrafficHub-obsidian/04-Database/autolead|autolead.db]]
- [[материалы/документы/TrafficHub-obsidian/04-Database/control|control.db]]
- [[материалы/документы/TrafficHub-obsidian/04-Database/traffic|traffic_dashboard.db]]
