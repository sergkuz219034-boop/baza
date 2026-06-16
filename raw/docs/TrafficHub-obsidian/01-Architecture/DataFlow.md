# Data Flow

## Полный цикл обработки лида

```mermaid
flowchart LR
    A[Rabota.ru API] -->|Отклики| B[Сбор]
    A -->|Автоподбор| B
    B --> C[Нормализация]
    C --> D[Дедупликация]
    D --> E[Скоринг]
    E --> F[(autolead.db)]
    F --> G[Google Sheets: "Все лиды"]
    F --> G2[Google Sheets: "Резюме"]
    F --> H[Playwright Autofill]
    H --> I[CPA Offer]
    F --> J[Rabota.ru Invite]
```

## Этапы

1. **Сбор**: `rabota_api.py` — OAuth2, пагинация, автоподбор.
2. **Обработка**: `data_processor.py` — очистка телефонов (+7), извлечение полей.
3. **Дедупликация**: по телефону и email.
4. **Скоринг**: [[Scoring]] — свежесть, совпадение вакансии, пол, город, телефон.
5. **Экспорт**: в Google Sheets и/или автозаполнение форм.
   - основной поток пишет нормализованные лиды в рабочий лист;
   - raw-резюме кандидатов дополнительно пишутся в отдельную вкладку `Резюме` того же workbook.
6. **Приглашение**: auto-invite через Rabota.ru API.

## Retry Queue

Неудачные отправки форм попадают в `retry_queue` -> повтор с exponential backoff.

## Связанное

- [[01-Architecture/Overview|Архитектура]]
- [[02-Modules/RabotaAPI|Rabota.ru API]]
- [[02-Modules/SheetsSync|Google Sheets]]
- [[02-Modules/VbivBot|Playwright Vbiv Bot]]
