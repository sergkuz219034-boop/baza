# Offer Mapping

## Формат

Live runtime читает локальные офферы из user-scoped `offer_mapping` в control-store.

```json
[
  {
    "name": "Offer Name",
    "target_url": "https://partner.com/form",
    "partner": "lovko|leadsu|tilda|general",
    "vacancy_ids": [123, 456],
    "vacancy_names": ["Менеджер", "Оператор"],
    "daily_limit": 100
  }
]
```

## Поля

| Поле | Описание |
|------|----------|
| `name` | Название оффера |
| `target_url` | URL формы для заполнения |
| `partner` | Внутренний engine hint (`lovko`, `leadsu`, `tilda`, `general`) |
| `vacancy_ids` | ID вакансий с Rabota.ru для маппинга |
| `vacancy_names` | Названия вакансий (alias) |
| `daily_limit` | Лимит отправок в день |

## Runtime notes

- Пользовательский лог должен оперировать названием оффера, а не названием внутреннего движка.
- `ВкусВилл`, `Самокат`, `Онекта`, `Воксис` — это офферы/маршруты.
- `Lovko`, `Leads.su`, `Tilda` — только способ заполнения.
- Если `partner/platform` пусты, рантайм теперь восстанавливает движок по `name + target_url`.
- При ответе `disabled.html` канонический статус оффера: `Оффер отключен`.

## Related

- [[05-Configuration/Config|Config]]
- [[02-Modules/VbivBot|Playwright Vbiv Bot]]
- [[01 Расследования/2026-06-15 Platform fallback, disabled offer status и live debug прогон офферов]]
