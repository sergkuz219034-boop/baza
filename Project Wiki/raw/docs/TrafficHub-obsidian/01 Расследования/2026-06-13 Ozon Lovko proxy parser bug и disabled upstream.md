## Симптом

- Ozon в Autolead не открывался даже при включённом proxy.
- Пользователь подтвердил, что вручную через proxy форма Ozon открывается.
- Live runtime на сервере получал `timeout`, `chrome-error://chromewebdata/` или `disabled.html`.

## Зона системы

- `/root/TrafficHub/modules/vbiv_bot.py`
- `/root/TrafficHub/api/routers/settings.py`
- `/root/TrafficHub/modules/platforms/lovko.py`
- внешний upstream `tracking.lovko.pro`

## Гипотеза

- В продукте было сразу две проблемы:
  1. browser-runner неправильно разбирал proxy формата `host:port:user:pass`;
  2. даже после исправления parser текущий Ozon tracking route может оставаться отключённым у партнёрки.

## Проверка

- По live-коду подтверждено:
  - `_normalize_proxy_url()` в `api/routers/settings.py` конвертировал `host:port:user:pass` в `socks5://user:pass@host:port`;
  - `_playwright_proxy_from_config()` в `modules/vbiv_bot.py` отбрасывал `socks5://user:pass@host:port` как неподдерживаемый для Playwright.
- Значит browser-runner фактически запускался без proxy, хотя в UI proxy считался включённым.
- Выполнена live-правка:
  - `host:port:user:pass` теперь нормализуется в `http://user:pass@host:port`;
  - browser-runner понимает и legacy-формат `socks5://user:pass@host:port`, но интерпретирует его как HTTP proxy для совместимости.
- После деплоя внутри `autolead_server_bot` подтверждено:
  - `_playwright_proxy_from_config({'rabota_ru': {'proxy_enabled': True, 'proxy_url': '217.29.62.68:8000:uE0D08:LZCcvM'}})`
    возвращает `{'server': 'http://217.29.62.68:8000', 'username': 'uE0D08', 'password': 'LZCcvM'}`;
  - тот же результат получается и для legacy-строки `socks5://uE0D08:LZCcvM@217.29.62.68:8000`.
- Далее выполнен live smoke через Chromium + proxy + тот же anti-detect context, что использует Autolead.
- Результат smoke:
  - final URL: `https://tracking.lovko.pro/disabled.html`
  - title: `Disabled`
  - поля анкеты отсутствуют.
- Дополнительно через `curl -L -x http://uE0D08:LZCcvM@217.29.62.68:8000 ...` подтвержден redirect на `disabled.html`.
- 13.06.2026 пользователь передал новый URL:
  - `https://tracking.lovko.pro/click?pid=4126&offer_id=22`
- Повторный live smoke через тот же proxy и тот же browser-runner подтвердил:
  - final URL: `https://vakansii-ozon.ru/vse-goroda/rabotnik-sklada-lovko/...`
  - title: `Вакансии в OZON: Работник склада`
  - в DOM присутствуют:
    - `input[name='lastname']`
    - `input[name='firstname']`
    - `input[name='mobile_phone']`
    - `select[name='citizenship']`
    - `input[name='birthdate']`
    - `input[name='vacancy_id']`
    - `button[aria-label='Отправить форму']`
- Дополнительно исправлен edge-case parser:
  - `http://host:port@user:pass`
  - `host:port:user:pass`
  - `http://user:pass@host:port`
  теперь приводятся к одному рабочему browser-proxy представлению.

## Наблюдение

- Внутренняя ошибка продукта действительно была:
  - proxy parser ломал browser-only офферы, включая Ozon/Lovko.
- Эта ошибка исправлена.
- Но после исправления сервер всё равно получает `disabled.html` именно от партнёрского маршрута `tracking.lovko.pro/click?...`.
- Следовательно, текущий blocking factor уже внешний, а не внутренний.

## Вывод

- Исправлена подтверждённая серверная ошибка:
  - Playwright теперь реально использует proxy с авторизацией для строк формата:
    - `host:port:user:pass`
    - `http://host:port@user:pass`
    - `http://user:pass@host:port`
    - legacy `socks5://user:pass@host:port`
- Старые Ozon routes `pid=41266` и `pid=4161` действительно проблемные/disabled для live runtime.
- Новый route `pid=4126` рабочий и открывает реальную форму Ozon на сервере.
- Для runtime добавлена явная диагностика `disabled.html` в `lovko.py`, чтобы лог больше не маскировал это как абстрактный timeout или “форма не подтверждена”.

## Следующий шаг

- Заменять Ozon `target_url` на:
  - `https://tracking.lovko.pro/click?pid=4126&offer_id=22`
- Если снова появятся `disabled.html` или timeout:
  - сначала проверять, не откатился ли URL обратно на старые `pid=41266` / `pid=4161`;
  - затем проверять proxy-строку пользователя и live smoke через тот же browser-runner.
