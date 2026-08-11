# Playwright BrowserManager

## Симптом

Во время рассылки `modules/vbiv_bot.py` создавал отдельный Chromium для каждой анкеты. При закрытии возникали `Task was destroyed but it is pending` и `TargetClosedError`; на малом сервере это повышало риск memory pressure.

## Зона системы

- `modules/vbiv_bot.py:run_campaign` — синхронное заполнение партнёрских форм.
- `traffic_hub/services/lovko_scraper.py` — асинхронный Lovko scraper.
- Live на 2026-08-11: `autolead_bot`, `worker`, AccountManager, Caddy, PostgreSQL и Redis healthy; в idle Chromium отсутствовал. `127.0.0.1:8080/api/health` отвечает `ok`.

## Гипотеза

Частый launch/close Chromium, а не постоянная утечка в idle, создаёт пики памяти и teardown warning.

## Проверка

- `run_campaign` имеет один `sync_playwright()` на campaign, но `pw.chromium.launch()` внутри каждого offer.
- Каждый offer уже получает отдельный `browser.new_context()` в `_make_context`.
- Lovko router создаёт отдельный `LovkoScraper` на запрос и закрывает его в `finally`; module-global singleton не использовался.
- SuperJob подключается к внешнему AdsPower CDP. Его нельзя закрывать или объединять с локальным Chromium.
- AccountManager и legacy Kwork живут в другом container/границе с OAuth/cookie semantics; в этот change не включены.

## Вывод

Добавлен `utils/browser_manager.SyncBrowserManager` для одного `sync_playwright()` lifetime:

- browser pool разделён на `direct` и `form-proxy`, без логирования proxy credentials;
- каждая анкета получает новый context/page, page закрывается раньше context;
- `MAX_BROWSER_CONTEXTS=2` по умолчанию; `BROWSER_MAX_LIFETIME_MINUTES=45`, `BROWSER_MAX_TASKS=75`;
- disconnected/closed browser перезапускается; idle expired browser recycle; campaign finalizer закрывает все browser;
- Lovko закрывает context, browser, playwright именно в таком порядке и больше не создаёт ненужный global scraper.

Это scoped pool: синхронный Playwright не передаётся между worker threads или jobs. Такой глобальный singleton небезопасен для greenlet runtime.

## Следующий шаг

Release 2026-08-11: GitHub Build, CI и Extended checks зелёные; app/worker переведены на `627de0fb51c896996a3cf204434fcb8752a744ab`. После restart оба healthy, `/api/health` возвращает `ok`, idle Chromium process count `0`.

Обнаружен infrastructure debt: root deploy wrapper использовал устаревший GHCR credential, поэтому `docker compose pull` получил `unauthorized`. CI-published image существует; для этого release создан локальный image из exact checked SHA с тем же immutable tag и выполнен `docker compose up -d --no-build autolead_bot worker`. Не делать package публичным. Отдельно выдать root deploy credential только с `read:packages` и заменить `/home/github-runner/.docker/config.json` через защищённый секрет.

Дальше: сравнить peak RSS/container memory во время полного цикла, убедиться в отсутствии новых teardown warnings. Отдельно исправлять AccountManager legacy Kwork proxy (`browser.new_context(proxy=...)` не поддерживает proxy semantics) без смешивания с TrafficHub form runner.
