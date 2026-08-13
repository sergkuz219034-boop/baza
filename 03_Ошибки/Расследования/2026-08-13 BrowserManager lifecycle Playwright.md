# BrowserManager lifecycle Playwright

## Симптом

Долгие Autolead-циклы создавали Chromium на каждую форму. Это повышало пики RAM/CPU и оставляло риск teardown-артефактов.

## Зона системы

`modules/vbiv_bot.py`, `utils/browser_manager.py`, subprocess worker.

## Проверка

- `vbiv_bot` использует scoped `SyncBrowserManager` внутри одного `sync_playwright` campaign.
- Браузеры разделены по profile `direct` и `form-proxy`; каждый lead получает новый context/page.
- `WORKER_MAX_PARALLEL_OWNERS=2` в Compose ограничивает одновременно работающие worker-job; `MAX_BROWSER_CONTEXTS=2` ограничивает contexts внутри campaign.
- Отдельные вызовы остаются в Lovko async scraper, AccountManager OAuth, Kwork fallback и SuperJob CDP: это другие runtime/внешний browser, поэтому общий sync browser небезопасен.

## Наблюдение

- До улучшения BrowserManager уже переиспользовал browser внутри совместимого Autolead job, но не давал полного lifecycle status/наблюдаемости.
- При ошибке `new_page()` после `new_context()` мог остаться частично созданный context.
- Runtime bootstrap и diagnostic probes используют Playwright только для поиска/проверки executable, не для бизнес-сессий.
- `utils/playwright_runtime.py` по умолчанию ставил полный `chromium`, если browser отсутствовал; это противоречило цели использовать Headless Shell на сервере.

## Вывод

Канонический form-runner использует browser pool без смешения cookies и proxy. Общий browser между sync и async процессами не реализуется намеренно: это нарушило бы thread/process ownership Playwright и proxy/account isolation.

## Следующий шаг

`f67e86803` уже добавил lifecycle-логи без секретов, status counters, cleanup частичного context и regression tests. В `codex/playwright-headless-shell` bootstrap изменён на `playwright install --only-shell chromium`; полный Chromium требует `PLAYWRIGHT_FULL_CHROMIUM=1`. Требуется CI, deploy и проверка live image/health.

## Связи

[[Автосброс устаревшей блокировки задач]]
