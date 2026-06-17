# 2026-06-01 patch-plan retry lead enrichment

## Анализ

Этот patch-plan описывает минимальный и локализованный путь исправления incident-класса:

- `нет оффера для vacancy_id: ... ()`

без прямого вмешательства в недоступный `modules.vbiv_bot`.

Основание:

1. matching `vacancy_id` в `offer_mapping` подтверждены;
2. retry path несёт урезанный lead payload;
3. обычный backlog lead уже содержит больше полей, которые потенциально важны для resolver logic.

## Причина

### Проблема

- Описание проблемы:
  - retry lead передаётся в sender в более бедной форме, чем обычный lead;
  - sender-boundary, вероятно, теряет возможность корректно сопоставить оффер по vacancy context.
- Первопричина:
  - в `process_retry_queue()` lead восстанавливается только частично;
  - в доступном коде нет enrichment шага из локальной `leads`-таблицы.
- Критичность: `High`
- Возможные последствия:
  - terminal `SKIP` при фактически существующем mapping;
  - накопление ложных retry;
  - неверная диагностика как “нет конфигурации”.
- Рекомендуемое исправление:
  - best-effort enrichment retry lead из `leads` table перед вызовом `run_sender()`.

## План исправления

Минимальный scope:

1. В [utils/database.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/utils/database.py)
- добавить новый helper, например:
  - `get_latest_lead_context_by_phones(...)`

2. Helper должен возвращать по нормализованному телефону:
- `vacancy`
- `city`
- `gender`
- `lead_date`
- `vacancy_id`
- `response_id`
- `resume_id`
- `source_type`

3. В [services/leads_service.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/services/leads_service.py)
- в `process_retry_queue()` перед циклом:
  - собрать телефоны `due_retries`
  - загрузить `lead_context_by_phone`

4. При сборке `retry_lead`:
- использовать данные из retry item как приоритетные
- недостающие поля брать из `lead_context_by_phone`

5. Не менять:
- `run_sender()`
- `run_campaign()`
- `offer_mapping`
- queue schema

## Diff

Ниже не готовый applied patch, а ready-to-apply diff-направление.

### 1. Новый helper в `utils/database.py`

```diff
def get_latest_lead_context_by_phones(phones: set[str] | list[str] | tuple[str, ...]) -> dict[str, dict]:
    """
    Возвращает последний контекст лида по нормализованному телефону.
    Нужен для enrichment retry payload перед повторной отправкой.
    """
    normalized = {_normalize_phone_key(phone) for phone in phones if _normalize_phone_key(phone)}
    if not normalized:
        return {}

    owner_sql, owner_params = _owner_filter_sql()
    db_phones = sorted(normalized | {f"+7{phone}" for phone in normalized})
    placeholders = ",".join("?" for _ in db_phones)
    sql = f"""
        SELECT phone, vacancy, city, gender, lead_date, vacancy_id, response_id, resume_id, source_type
        FROM leads
        WHERE {owner_sql} AND phone IN ({placeholders})
        ORDER BY id DESC
    """

    result = {}
    with _conn() as con:
        rows = con.execute(sql, [*owner_params, *db_phones]).fetchall()

    for row in rows:
        phone_key = _normalize_phone_key(row["phone"])
        if not phone_key or phone_key in result:
            continue
        result[phone_key] = {
            "vacancy": row["vacancy"] or "",
            "city": row["city"] or "",
            "gender": row["gender"] or "",
            "lead_date": row["lead_date"] or "",
            "vacancy_id": row["vacancy_id"],
            "response_id": row["response_id"],
            "resume_id": row["resume_id"],
            "source_type": row["source_type"] or "",
        }
    return result
```

### 2. Подготовка enrichment map в `process_retry_queue()`

```diff
 def process_retry_queue(config: dict) -> dict:
     from utils.state import is_stop_requested
-    from utils.database import get_due_retries, load_send_history, remove_from_retry_queue
+    from utils.database import (
+        get_due_retries,
+        get_latest_lead_context_by_phones,
+        load_send_history,
+        remove_from_retry_queue,
+    )

     due_retries = get_due_retries()
     if not due_retries:
         return {"retried": 0, "sent": 0, "skipped": 0, "errors": 0, "duplicates": 0}

+    lead_context_by_phone = get_latest_lead_context_by_phones(
+        {str(item.get("phone", "")).strip() for item in due_retries}
+    )
```

### 3. Enrichment при сборке `retry_lead`

```diff
        phone_key = _normalize_phone_key(phone)
        lead_ctx = lead_context_by_phone.get(phone_key, {})

        vacancy_id = item.get("vacancy_id") or lead_ctx.get("vacancy_id") or 0
        response_id = item.get("response_id") or lead_ctx.get("response_id") or 0
        resume_id = item.get("resume_id") or lead_ctx.get("resume_id") or 0
        city = str(item.get("city", "")).strip() or str(lead_ctx.get("city", "")).strip() or "Москва"
        vacancy_name = str(lead_ctx.get("vacancy", "")).strip()
        gender = str(lead_ctx.get("gender", "")).strip()
        lead_date = str(lead_ctx.get("lead_date", "")).strip()
        source_type = "response" if response_id else str(lead_ctx.get("source_type", "") or "")

        retry_lead = {
            "Фио": str(item.get("full_name", "")).strip(),
            "Номер": phone,
            "Вакансия": vacancy_name,
            "Город": city,
            "Пол": gender,
            "Дата": lead_date,
            "_source_type": source_type,
            "_raw_data": {
                "vacancy_id": vacancy_id,
                "response_id": response_id,
                "resume_id": resume_id,
            },
        }
```

### 4. Нормализация `base_offer["vacancy_ids"]`

Текущее поведение уже почти достаточно хорошее, но diff безопасно дополнить единым источником `vacancy_id`:

```diff
-        vacancy_id = item.get("vacancy_id") or 0
+        vacancy_id = item.get("vacancy_id") or lead_ctx.get("vacancy_id") or 0
```

## Риски

Основные побочные эффекты:

1. Lookup по телефону может подтянуть не тот контекст, если номер повторно использовался для другой вакансии.
2. Если latest row в `leads` уже нерелевантна, vacancy title будет устаревшим.
3. Если sender на самом деле ждёт более сложный raw structure, enrichment улучшит ситуацию частично, но не полностью.

Почему план всё ещё безопасен:

- обычная send path не меняется;
- queue schema не меняется;
- fallback behaviour можно сохранить полностью;
- если enrichment ничего не нашёл, система ведёт себя как сейчас.

## Проверка после исправления

Минимальный checklist после внедрения:

1. Retry lead перед `run_sender()` содержит:
- `Вакансия`
- `Город`
- `Пол`
- `Дата`
- `_raw_data.vacancy_id`

2. Инцидентные `vacancy_id`:
- `54244364`
- `54267737`
- `54279842`
- `54279727`

больше не уходят в `нет оффера ... ()`.

3. Если lookup в `leads` не находит запись:
- retry path не падает;
- поведение остаётся деградированным, но рабочим.

4. Обычная рассылка не меняет поведение.

5. `retry_queue` не начинает дублировать или искажать статистику.

## Дополнительные улучшения

После этого шага логично:

1. дополнить `Wave 5` execution-pack секцией `payload integrity`;
2. при появлении полного `vbiv_bot` source сверить, нужны ли ещё:
   - top-level `vacancy_id`
   - `vacancy` внутри `_raw_data`
   - дополнительная нормализация типов
3. если проблема подтвердится массово, рассмотреть второй этап:
   - сделать retry records self-contained прямо на уровне `add_to_retry_queue(...)`.
