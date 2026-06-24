# Runtime doctor

## Назначение
`tools/doctor.py` даёт быстрый снимок server runtime без ручного обхода контейнеров.

## Где запускать
Только на сервере в `/root/TrafficHub`.

```bash
./tools/doctor.py
./tools/doctor.py --json
```

## Что проверяет
- состояние server git repo;
- drift от `origin/main`;
- `docker compose ps`;
- `/api/health`;
- PostgreSQL runtime-хранилища;
- Redis/job queue;
- наличие `rg`, `graphify`, `python`, `python3`.

## Exit codes
- `0` — критичных проблем нет;
- `1` — есть warning;
- `2` — есть critical failure.

## Важное ограничение
`graphify` может отсутствовать на сервере. Это warning, потому что Graphify используется локально по snapshot, а не как runtime dependency.

## Проверенный статус
На live-сервере после commit `70b761e12`:

- `API health` — OK;
- PostgreSQL runtime-хранилища — OK;
- job queue — OK;
- `python` и `python3` доступны;
- warning остаётся только по отсутствующему server-side `graphify`.

## Связанные заметки
- [[Graphify architecture scan]]
- [[Runtime Inspector]]
- [[Remote ops tools]]
