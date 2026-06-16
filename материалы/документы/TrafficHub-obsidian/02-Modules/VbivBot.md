# Playwright Vbiv Bot

Файл: `modules/vbiv_bot.py`

## Назначение

Автоматическое заполнение веб-форм (CPA offers) через Playwright (headless Chromium).

## Anti-detection

- `navigator.webdriver = false`
- Локаль `ru-RU`
- Кастомный User-Agent
- От `2026-06-15` live runtime больше не ограничивается `per-lead context`.
- Подтверждённый contract:
  - каждая анкета / каждый оффер запускается в отдельном Chromium browser instance;
  - после заполнения browser закрывается сразу;
  - цель — не наследовать предыдущую partner session и считать click уникальным.
- Live source-of-truth на `2026-06-16`:
  - в `modules/vbiv_bot.py` helper `_launch_browser()` вызывает `pw.chromium.launch(...)`;
  - внутри offer-loop перед каждым `platform_impl.fill()` выполняется `browser = _launch_browser(use_proxy=...)`;
  - в `finally` этого же блока выполняется `browser.close()`.

## Платформы

| Платформа | Модуль |
|-----------|--------|
| **Lovko** | `betaonline.ru` |
| **Leads.su** | Voxis / Onekta |
| **Tilda** | Сайты на Tilda |
| **Generic** | Любая форма |

На live runtime от `2026-06-15` подтверждено:

- user-facing лог не должен показывать `tilda` / `lovko` / `leadsu` как будто это названия офферов;
- рантайм сначала использует `partner/platform`, а если metadata пустая, восстанавливает движок по `offer.name + offer.target_url`;
- `disabled.html` должен переводиться в persisted status оффера, а не оставаться только runtime-error.
- Для `leadsu` подтверждён отдельный режим нестабильности:
  - landing `pxl.leads.su -> partner page` может быть flaky через proxy;
  - success нельзя детектить по `first` element combined selector, нужно проверять любой видимый match.
- Для form proxy подтверждён owner/runtime-specific split:
  - глобальный proxy на все анкеты неверен;
  - `lovko/Ozon` требуют отдельного proxy-path;
  - `pxl.leads.su` / `Онекта` в live smoke открывались корректно без proxy и таймаутились через proxy.
- На `2026-06-16` дополнительно подтверждено:
  - `Онекта/Tilda` может успешно принять submit, но оставить `.js-successbox` в `display:none`;
  - поэтому общий success-path дополняется hidden-success fallback в `modules/platforms/tilda.py`;
  - этот fallback нельзя переносить на все платформы, он привязан к конкретному Tilda runtime-pattern.

## Retry Queue

При ошибке — скриншот + HTML + text диагностика. Лид уходит в `retry_queue` для повторной отправки.

## Disabled offers

- `disabled.html` — это прикладной partner-status, а не generic DOM failure.
- Такой оффер должен:
  - логироваться как `Оффер отключен`;
  - исключаться из следующих рассылок;
  - жить в `offer_mapping` со статусом `disabled`.

## Связанное

- [[01-Architecture/DataFlow|Data Flow]]
- [[05-Configuration/Offers|Offer Mapping]]
- [[01 Расследования/2026-06-15 Platform fallback, disabled offer status и live debug прогон офферов]]
- [[01 Расследования/2026-06-15 Voxys leadsu success selector и intermittent goto timeout]]
- [[01 Расследования/2026-06-16 Онекта Tilda hidden successbox и отдельный browser на оффер]]
