# 2026-06-14 Debug HTML показал maxlength в Voxys и хрупкий submit-path Tilda

## Симптом

- В live `app_log` и debug-артефактах повторялись ошибки:
  - `Воксис`: `leadsu: кнопка submit не найдена`, `leadsu: форма не подтверждена после отправки`
  - `Онекта`: `tilda: кнопка submit не найдена`, `tilda: форма не подтверждена после отправки`
- На сервере накапливались свежие артефакты:
  - `/root/TrafficHub/data/debug/debug_Воксис_*.html/.png`
  - `/root/TrafficHub/data/debug/debug_Онекта_*.html/.png`

## Зона системы

- Live code:
  - `/root/TrafficHub/modules/platforms/leadsu.py`
  - `/root/TrafficHub/modules/platforms/tilda.py`
  - `/root/TrafficHub/modules/platforms/base.py`
- Runtime evidence:
  - `/root/TrafficHub/data/debug/debug_Воксис_20260614_204742.html`
  - `/root/TrafficHub/data/debug/debug_Онекта_20260614_204617.html`
  - worker log `traffichub_worker`

## Гипотеза

- `Воксис` валится не только из-за сети, но и из-за client-side validation на поле имени/фамилии.
- `Онекта` страдает от хрупкого Tilda submit-path:
  - слишком узкий поиск поля/кнопки;
  - слабый post-submit success detection;
  - submit может проходить через popup/requestSubmit-path, а не только через прямой `button.click()`.

## Проверка

- Read-only разбор `debug_Воксис_20260614_204742.html` подтвердил:
  - форма `#vacancy_form`
  - submit-кнопка реально есть: `button#send_form`
  - hidden success popup есть в DOM:
    - `#hidden-content`
    - текст `Ваша анкета принята`
  - у поля `fname` в debug HTML был visible validation error:
    - `class="input100 error"`
    - `<label id="fname-error" class="error">Максимальное число символов - 24</label>`
- Это совпало с live lead:
  - `Патрик Джонатан Фиде Aka Фиде Aka`
  - ошибка валидации воспроизводима логически: `first_name` мог содержать хвост полного ФИО длиной > 24.
- Read-only разбор `debug_Онекта_20260614_204617.html` подтвердил:
  - форма `form731751918`
  - submit-кнопка реально есть:
    - `button[type="submit"].t-submit`
    - текст `Откликнуться`
  - success DOM есть в шаблоне:
    - `.js-successbox.t-form__successbox`
    - текст `Спасибо! Ваши данные успешно отправлены.`
  - required-поля подтверждены в HTML:
    - `input[name="name"][data-tilda-req="1"]`
    - `select[name="гражданство"][data-tilda-req="1"]`
    - `input[name="Checkbox"][data-tilda-req="1"]`
    - `input[name="Checkbox_2"][data-tilda-req="1"]`
- Следствие:
  - `tilda: кнопка submit не найдена` была ложной диагностикой: кнопка в DOM есть;
  - проблема была в хрупком runtime-path поиска/сабмита/подтверждения, а не в отсутствии формы.

## Наблюдение

- Worker log до фикса уже показывал, что эти офферы не «мертвы» целиком:
  - часть `Воксис` и `Онекта` успешно проходила;
  - падали частные кейсы.
- Это важный разделитель:
  - массовая поломка платформы отсутствовала;
  - были runtime edge cases по данным лида и brittle DOM-path.

## Вывод

- Для `Воксис` primary fix:
  - в `modules/platforms/leadsu.py` добавлена нормализация имени/фамилии под лимит `24` символа;
  - если строка длиннее лимита, берётся первый токен или усечённая безопасная версия.
- Для `Воксис` secondary fix:
  - success detection расширен на hidden/popup path:
    - `#hidden-content`
    - `.fancybox__container`
    - `.pu_container`
    - `[data-fancybox-close]`
- Для `Онекта` / Tilda:
  - в `modules/platforms/tilda.py` добавлен более устойчивый поиск полей через `_wait_for_any(...)`;
  - submit-path расширен:
    - `.t-submit`
    - `button[type="submit"]`
    - `input[type="submit"]`
    - role/button regex
    - JS fallback
    - `form.requestSubmit(...)`
  - success detection расширен на popup-контейнеры Tilda.
- Дополнительный Tilda fix:
  - после ввода маскированного телефона в `tildaspec-phone-part[]` backend теперь принудительно синхронизирует hidden `input[name="Phone"]`.

## Следующий шаг

- При следующем live фейле сначала сверять новый `debug_*.html`:
  - есть ли visible validation error;
  - есть ли success popup в DOM;
  - есть ли фактическая submit-кнопка.
- Если снова будет падать `Онекта`, следующая точка проверки:
  - AJAX-response path Tilda после `requestSubmit`, а не селекторы формы.

## Обновление 2026-06-15

- Controlled smoke без submit на live server подтвердил:
  - `Voxys_alex`
    - direct: `ok`
    - proxy: `ok`
    - форма и `#send_form` доступны стабильно.
  - `Onecta_alex`
    - direct: `ok`
    - proxy: `ok`
    - Tilda landing открывается стабильно, форма и `.t-submit` доступны.
  - `Ozon_alex`
    - direct: `Page.goto: net::ERR_TIMED_OUT`
    - proxy: `ok`
    - landing открывается только через proxy.

## Обновлённый вывод

- После platform-fix `Voxys` и `Onecta` больше не выглядят как navigation-broken offers:
  - их landing pages открываются и дают ожидаемый DOM.
- Остаточный сетевой дефект отделён от fill-path:
  - `Ozon` без proxy воспроизводимо падает ещё на `goto`;
  - это не баг заполнения формы, а network/open-page проблема.
