# utils

Общие инфраструктурные утилиты.

## Что здесь лежит

- [config_loader.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/config_loader.py) — минимальный reader config.json
- [database.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/database.py) — работа с БД
- [control_store.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/control_store.py) — control-store слой
- [state.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/state.py) — runtime state и stop/event
- [user_context.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/user_context.py) — текущий user scope
- [license.py](C:/Users/Арт/Desktop/TrafServer/remote_files/utils/license.py) — license / hwid / cloud config

## Как читать

1. Для config начинай с `config_loader.py`.
2. Для owner-scope и runtime state смотри `user_context.py` и `state.py`.
3. Для хранения и синхронизации переходи в `database.py`, `control_store.py` и `license.py`.
