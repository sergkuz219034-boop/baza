# Lovko tracking timeout cascade

## Симптом

В логах Autolead:

- `Страница оффера не открылась: Page.goto: net::ERR_TIMED_OUT at https://tracking.lovko.pro/fjk03d`
- после этого появлялись вторичные ошибки вида `Target page, context or browser has been closed`
- при нажатии stop в UI появлялись красные field-level строки `leadsu Телефон`, `leadsu Чекбокс`

## Зона системы

- `modules/vbiv_bot.py`
- `modules/platforms/leadsu.py`
- Playwright navigation для партнёрских tracking links `tracking.lovko.pro`

## Гипотеза

`tracking.lovko.pro` не считался медленным/нестабильным Lovko route, поэтому навигация получала недостаточный retry/timeout профиль. После timeout или stop закрытый Playwright context продолжал давать field-level ошибки внутри LeadsuPlatform.

## Проверка

В live repo `/root/TrafficHub` подтверждено:

- `_is_slow_lovko_route()` до фикса учитывал `jobs-samokat.ru`, `logystpartner.ru`, `ozon`, но не `tracking.lovko.pro`;
- `_is_permanent_form_failure()` не классифицировал `Target page/context/browser has been closed` как transient;
- `LeadsuPlatform.fill()` логировал ошибки телефона/чекбокса даже если page/context уже закрыт.

## Наблюдение

Первичная ошибка — недоступность/timeout партнёрского tracking URL. Ошибки `Target page/context/browser has been closed` были каскадом после закрытого Playwright context, а не самостоятельной причиной.

## Вывод

Для `tracking.lovko.pro` нужен slow-route navigation профиль и чистая обработка закрытого context, чтобы:

- не ломать весь цикл из-за одного нестабильного партнёрского URL;
- не писать несколько красных вторичных ошибок;
- не считать закрытый context постоянной form-failure.

## Следующий шаг

Наблюдать свежие логи Autolead после деплоя. Если `tracking.lovko.pro` продолжит регулярно timeout, проверять уже сетевую доступность партнёрки/прокси, а не форму Leadsu.

## Фикс

Product commit: `c87e2afa2` `fix: handle lovko tracking timeouts cleanly`.

Изменения:

- `tracking.lovko.pro` и `lovko.pro` добавлены в slow Lovko route;
- закрытый Playwright page/context/browser распознаётся как transient;
- при stop + closed context ошибка не считается form failure;
- `LeadsuPlatform` останавливает заполнение одной понятной причиной, если page уже закрыт перед телефоном/чекбоксом.

## Проверка фикса

```bash
docker compose exec -T autolead_bot python -m pytest tests/test_vbiv_bot_runtime_errors.py -q
```

Результат: `3 passed`.

Live:

- `autolead_bot` healthy;
- `worker` healthy;
- `/api/health` возвращает `status=ok`;
- local HEAD и remote HEAD: `c87e2afa2`.

## Уточнение 2026-06-26: regression в CI

### Симптом

После расширения slow-route правила GitHub Actions `CI / validate` упал на тесте `tests/test_vbiv_bot_navigation.py::test_slow_lovko_route_does_not_mark_generic_lovko_offer_slow`.

### Зона системы

- `modules/vbiv_bot.py`
- `_is_slow_lovko_route(offer_name, current_url)`
- GitHub Actions `CI / validate`

### Гипотеза

Правило `tracking.lovko.pro`/`lovko.pro` стало слишком широким: оно переводило в slow-mode все Lovko-ссылки, включая обычный offer URL `offer_id=34`, хотя slow-mode нужен только для коротких tracking links и подтверждённых проблемных маршрутов.

### Проверка

Подтверждено тестами:

- `https://tracking.lovko.pro/fjk03d` должен оставаться slow-route;
- `https://tracking.lovko.pro/click?pid=4161&offer_id=22&sub1=1` должен оставаться slow-route для Ozon;
- `https://tracking.lovko.pro/click?pid=4161&offer_id=34&sub1=1` не должен считаться slow-route для обычного Lovko-оффера.

### Наблюдение

Первичный фикс был правильным по цели, но слишком грубым по условию домена. Домен Lovko сам по себе не является достаточным признаком slow-route.

### Вывод

Для Lovko нельзя включать slow-mode по всему домену. Текущее подтверждённое правило:

- short tracking link без `offer_id=` — slow-route;
- `offer_id=22` или название `Ozon` — slow-route;
- `Самокат`, `jobs-samokat.ru`, `logystpartner.ru` — slow-route;
- остальные Lovko offer URLs — обычный режим, пока runtime не докажет обратное.

### Следующий шаг

Если появится новый нестабильный Lovko offer, добавлять точечный признак и тест, а не расширять правило на весь `lovko.pro`.

### Фикс

Product commits:

- `8ff851694` `fix: narrow lovko slow route detection`
- `c7affc26e` `ci: provide hermes dummy auth for compose validation`

Проверка:

- host: `python -m pytest -q tests/test_vbiv_bot_navigation.py tests/test_vbiv_bot_runtime_errors.py` → `6 passed`;
- container after rebuild: `docker exec traffichub_app python -m pytest -q tests/test_vbiv_bot_navigation.py tests/test_vbiv_bot_runtime_errors.py` → `6 passed`;
- live `/api/health` → `status=ok`;
- GitHub check-runs на `c7affc26e`: `validate`, `windows-launcher`, `build-and-push` → `success`.
