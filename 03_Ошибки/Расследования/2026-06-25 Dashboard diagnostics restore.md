# Dashboard diagnostics restore

## Симптом

В dashboard не было явной точки входа для диагностических инструментов:

- Runtime Inspector;
- `doctor.py` для полной диагностики;
- Job Timeline;
- Explain Candidate.

## Зона системы

- UI: `dashboard/index.html`, `dashboard/app.js`, `dashboard/style.css`
- API: `api/routers/system.py`, `api/routers/jobs.py`, `api/routers/leads.py`
- CLI: `tools/doctor.py`, root-wrapper `doctor.py`

## Гипотеза

Инструменты не были полностью удалены, но часть функций была спрятана внутри `Admin панель`, а часть не имела UI-точки входа.

## Проверка

На live repo `/root/TrafficHub` подтверждено:

- `dashboard/index.html` содержал блоки `runtime-inspector-block` и `job-timeline-block` внутри `tab-admin`;
- `/api/system/runtime-inspector` существует в `api/routers/system.py`;
- `/api/jobs/timeline` существует в `api/routers/jobs.py`;
- `/api/leads/{lead_id}/explain` существует в `api/routers/leads.py`;
- `tools/doctor.py` существует, но root-команды `python3 doctor.py` не было.

## Наблюдение

Проблема была в навигации и UX dashboard:

- Runtime Inspector и Job Timeline были технически доступны, но спрятаны глубоко в admin;
- Explain Candidate имел backend endpoint, но не имел UI;
- `tools/doctor.py` был неочевиден для оператора, потому что команда ожидалась как `doctor.py`;
- host-level `doctor.py` проверяет Docker/runtime и должен запускаться на сервере, а не считаться полноценным из контейнерного dashboard API.

## Вывод

Диагностика должна быть отдельной admin-only вкладкой dashboard, а не частью таблицы аккаунтов.

Фикс в product repo:

- commit `6c541f4f7` `fix: restore dashboard diagnostics tools`;
- добавлена вкладка `Диагностика` в admin-навигации;
- добавлены UI-блоки Runtime Inspector, `doctor.py`, Job Timeline, Explain Candidate;
- добавлен root-wrapper `doctor.py`, который вызывает `tools.doctor.main`;
- добавлен best-effort endpoint `POST /api/system/doctor`;
- исправлен дублирующий `const enabled` в `dashboard/app.js`.

## Следующий шаг

- Полный host-level doctor запускать командой:

```bash
cd /root/TrafficHub && python3 doctor.py
```

- Dashboard-кнопка `Запустить из dashboard` является best-effort проверкой из контейнера. Если она возвращает warning/error по Docker, это не равно падению live-сервиса.

## Проверка фикса

- `node --check dashboard/app.js` — OK.
- AST parse для `api/routers/system.py`, `doctor.py`, `tools/doctor.py` — OK.
- Container tests:

```bash
docker compose exec -T autolead_bot python -m pytest tests/test_system_doctor.py tests/test_jobs_router.py tests/test_explain_candidate.py -q
```

Результат: `8 passed`.

- Live `/api/health` отвечает `status=ok`.
- Live static HTML содержит `nav-diagnostics`, `tab-diagnostics`, Runtime Inspector, `doctor.py`, Job Timeline, Explain Candidate.
