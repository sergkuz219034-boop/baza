# AccountManager

Отдельное приложение для управления аккаунтами и прокси.

## Структура

```
AccountManager/
├── api/           FastAPI app
├── dashboard/     HTML/CSS/JS frontend
├── database/      SQLAlchemy models
├── utils/         Checkers + proxy presets
│   ├── checker.py         -- Проверка живости аккаунтов
│   ├── tg_profiles.py     -- Импорт Telegram профилей
│   └── proxy_presets.py   -- Пресеты прокси (MTProto WS)
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Поддерживаемые платформы

- VK
- Telegram (включая MTProto WS прокси)
- Google
- MAX

## Запуск

```bash
cd AccountManager
docker compose up -d
```

или через `AccountManager.exe` (Windows Launcher).

## Связанное

- [[материалы/документы/TrafficHub-obsidian/06-Deployment/Docker|Docker]]
