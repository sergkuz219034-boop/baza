# Конфигурация

## Файлы

| Файл | Назначение |
|------|-----------|
| `secrets/config.json` | Основной конфиг (runtime) |
| `config.example.json` | Шаблон конфига |
| `config/settings.py` | Global settings + env vars |

## Источники

Конфиг мержится из двух источников:
1. Локальный `secrets/config.json`
2. Cloud-synced из `control.db` (`app_configs`)

Cloud имеет приоритет для некоторых полей.

## Секции

```json
{
  "rabota_ru": { "credentials": {}, "vacancies": [] },
  "google_sheets": { "sheet_url": "", "tab_name": "" },
  "vbiv": { "headless": true, "platforms": {} },
  "offer_mapping": [ { "name": "", "target_url": "", "partner": "" } ],
  "superjob": { "cdp_url": "", "vacancies": [] },
  "access": { "login": "", "password": "" },
  "tools": { "hr_chatbot": {} }
}
```

## Hot-reload

- Планировщик перечитывает каждые 30 секунд
- API использует TTL-кэш 5 секунд

## Связанное

- [[материалы/документы/TrafficHub-obsidian/05-Configuration/Offers|Offer Mapping]]
- [[материалы/документы/TrafficHub-obsidian/05-Configuration/License|Лицензирование]]
