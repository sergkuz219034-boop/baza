# Тесты

Файлы: `tests/`

## Тест-сьют

| Файл | Описание |
|------|----------|
| `test_auth_roles.py` | RBAC: viewer denied, operator allowed export, operator denied destructive |
| `test_config_merge.py` | SuperJob merge config: local preserved, cloud doesn't blank |
| `test_rabota_api_errors.py` | Error classification: 403/timeout/SSL/proxy, VPN hint cooldown |
| `test_offers_import_export.py` | Offer import/export validation |
| `test_settings_import_export.py` | Settings bundle import/export |

## CI

GitHub Actions (`ci.yml`):
```yaml
- pytest
- pip check
- docker compose config
- compile C# launcher (Windows)
```

## Запуск

```bash
pytest
```

## Live runtime

- Канонический test-runtime для server-side smoke:
  - container `autolead_server_bot`
  - запуск: `docker exec autolead_server_bot python -m pytest ...`
- На `2026-06-16` подтверждено:
  - `pytest` снова встроен в runtime image;
  - релевантный regression-срез
    - `test_sheets_queues.py`
    - `test_leads_service_sheets_flow.py`
    - `test_jobs_router.py`
    - `test_worker_parallel.py`
    - `test_offers_import_export.py`
  - прошёл как `33 passed`.
- Дополнительный targeted regression на `2026-06-16`:
  - `test_sheets_queues.py`
  - результат: `13 passed`
  - этим срезом отдельно подтверждён инвариант:
    - queue workbook `pending/processed` не fallback-ится в legacy `google_sheets.spreadsheet_id/spreadsheet_name`.
- Важное замечание:
  - если после очередного rebuild `python -m pytest` пропадает из container, wiki надо считать устаревшей до повторной live-проверки.

## Связанное

- [[06-Deployment/Docker|Docker]]
- [[03-API/Auth|Авторизация]]
- [[01 Расследования/2026-06-16 Pytest снова встроен в autolead_server_bot runtime image]]
