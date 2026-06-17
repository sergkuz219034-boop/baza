# tools

Локальные helper-утилиты для SSH, remote exec, push и диагностики.

## Главные инструменты

- [local_ssh.py](C:/Users/Арт/Desktop/TrafServer/tools/local_ssh.py) — локальный SSH helper
- [remote_exec.py](C:/Users/Арт/Desktop/TrafServer/tools/remote_exec.py) — выполнение команд на сервере
- [push_fix.py](C:/Users/Арт/Desktop/TrafServer/tools/push_fix.py) — точечная отправка фиксов
- [ssh_key_readiness.py](C:/Users/Арт/Desktop/TrafServer/tools/ssh_key_readiness.py) — проверка готовности ключей
- [hermes_telegram_user_bridge.py](C:/Users/Арт/Desktop/TrafServer/tools/hermes_telegram_user_bridge.py) — bridge для Hermes
- [hermes_bridge_selftest.py](C:/Users/Арт/Desktop/TrafServer/tools/hermes_bridge_selftest.py) — самопроверка bridge

## Запускные скрипты

- `run_hermes_telegram_user_bridge.ps1`
- `run_hermes_user_bridge_server.sh`
- `prepare_ssh_migration.ps1`
- `reset_hermes_chat_state.py`

## Чего тут не должно быть

- большие runtime-артефакты;
- временные unpack-каталоги;
- код приложения как отдельный локальный clone.
