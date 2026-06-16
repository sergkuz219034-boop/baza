# 2026-06-14 Leadsu blank DOM before submit on Voxys

## Симптом

- На реальном `alex/run` в live app-log появилась ошибка:
  - `Ошибка Воксис [6]: leadsu: кнопка submit не найдена`
- Ранее тот же оффер `Воксис` в этом же runtime проходил успешно или как `duplicate`.

## Зона системы

- Live code:
  - `/root/TrafficHub/modules/platforms/leadsu.py`
  - `/root/TrafficHub/modules/vbiv_bot.py`
- Debug artifacts:
  - `/root/TrafficHub/data/debug/debug_Воксис_20260614_155713.html`
  - `/root/TrafficHub/data/debug/debug_Воксис_20260614_155713.png`

## Гипотеза

- Проблема не обязательно в drift submit selector.
- Возможен промежуточный blank DOM после navigation, из-за которого submit искать уже не в чем.

## Проверка

- В live app-log для `alex` подтверждено:
  - до ошибки были и успешные кейсы:
    - `[OK] Оффер Ozon успешно заполнен!`
    - `[OK] Оффер Онекта успешно заполнен!`
    - `[OK] Оффер Воксис успешно заполнен!`
  - затем один из `Воксис` завершился ошибкой:
    - `leadsu: кнопка submit не найдена`
- По debug HTML подтверждено:
  - файл содержит только:
    - `<html><head></head><body></body></html>`
  - в артефакте отсутствуют:
    - `#send_form`
    - `vacancy_form`
    - `button`
    - `form`
    - тексты `Отправить`, `Откликнуться`
- Следствие:
  - это не обычный selector drift уже загруженной анкеты;
  - debug snapshot был снят на фактически пустой странице.
- После внесения recovery в `modules/platforms/leadsu.py` выполнен отдельный safe smoke без submit:
  - `alex / Воксис`
  - `10` открытий подряд
  - во всех `10/10` случаях до стадии submit было подтверждено:
    - `title = Работа в «VOXYS»`
    - `hasSendForm = true`
    - `visibleButtons` содержит `Отправить анкету`
    - `isBlank = false`
- Это не доказывает, что blank-case исчез полностью на production submit-path.
- Но подтверждает:
  - штатный route сейчас открывает форму стабильно;
  - blank-page recovery не ухудшил рабочий сценарий.

## Наблюдение

- `LeadsuPlatform` раньше считала `submit not found` финальной ошибкой.
- Для `Воксис` это слишком жёстко:
  - часть прогонов даёт нормальную форму;
  - часть прогонов схлопывается в blank DOM перед submit.

## Вывод

- На `2026-06-14` в live code добавлен recovery:
  - если перед submit страница выглядит как blank DOM или `chrome-error://chromewebdata/`,
  - `LeadsuPlatform` делает один `reload` + повторный поиск submit button
- Это не гарантирует, что upstream всегда оживёт.
- Но это убирает класс ложных fail, когда мы сдавались без попытки восстановить пустую страницу.
- На текущем safe smoke после фикса `Воксис` снова открывает форму стабильно `10/10` до submit-стадии.

## Следующий шаг

- Добавить unit/regression test на blank-page recovery для `LeadsuPlatform`.
- При следующем live инциденте сравнить:
  - стало ли меньше `leadsu: кнопка submit не найдена`
  - перестал ли debug HTML быть пустым body.
