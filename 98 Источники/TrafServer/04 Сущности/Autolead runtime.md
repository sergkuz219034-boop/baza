# Autolead runtime

Теги: #сущность

## Тип

Модуль

## Где находится

`remote_server_snapshot/main.py`

## Роль в системе

Запускает логирование, инициализацию локальных БД, background sync, планировщик и web dashboard. Это основной operational entrypoint системы.

## Входы

- env variables
- `control.db`
- локальный `config.json`
- secrets directory

## Выходы

- scheduler thread
- web dashboard
- файлы логов

## Зависимости

- [[Leads service]]
- [[Runtime database]]
- [[Control store]]

## Типовые сбои или риски

- неполный runtime snapshot;
- зависимость от скрытых модулей `api.server` и `config.settings`;
- сложный startup path.
