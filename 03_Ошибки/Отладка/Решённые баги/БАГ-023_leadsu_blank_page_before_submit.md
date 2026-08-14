# БАГ-023: leadsu/Voksis падал на пустой странице перед submit

## Симптом

У пользователей в live-логах повторялась ошибка:

- `leadsu: кнопка submit не найдена`
- затем `form-failure, retry queue пропущена`

По debug-артефактам `debug_Воксис_20260619_*.html` сохранялся пустой HTML:

- `<html><head></head><body></body></html>`

## Зона системы

- `modules/platforms/leadsu.py`
- `LeadsuPlatform._resolve_submit_button()`
- Playwright flow офферов `leads.su` / `Воксис`

## Гипотеза

Сбой происходил не из-за изменения CSS-селектора submit-кнопки, а раньше: страница оффера иногда схлопывалась в пустой DOM перед этапом submit. Текущий recovery делал только `reload`, но если reload тоже возвращал blank page, сценарий завершался permanent form-failure.

## Проверка

- На live-сервере debug HTML для последовательных падений `2026-06-19 20:29`, `20:32`, `21:01`, `21:03`, `21:04` имел размер `39` байт.
- Содержимое всех этих артефактов было пустым `body`, без формы и без кнопки.
- Код `leadsu.py` до фикса:
  - определял blank-page корректно;
  - делал `page.reload(...)`;
  - после второго blank-state сразу возвращал `None`.

## Наблюдение

Фикс:

- после неуспешного `reload` `LeadsuPlatform._resolve_submit_button()` теперь повторно открывает `offer.target_url`;
- затем повторно ждёт `load_state` и снова ищет submit-кнопку.

Добавлен regression test:

- `test_leadsu_resolve_submit_button_reopens_target_url_after_blank_reload`

Live-проверка после выкладки:

- `docker exec autolead_server_bot pytest -q tests/test_leadsu_blank_recovery.py tests/test_sheets_queues.py`
- результат: `26 passed`

Runtime-аудит 2026-06-21:

- product HEAD: `7bfc53694`;
- свежих `debug_Воксис_*` после `2026-06-20 12:26 MSK` нет;
- свежих `Воксис / кнопка submit / leadsu blank` строк в контейнерных логах после деплоя нет;
- в `autolead_retry_queue` были две старые истёкшие строки `admin / Воксис` с `retry_count=3`, `max_retries=3`;
- эти строки не были активной очередью, но были удалены cleanup-запросом;
- после cleanup active retry queue по всем пользователям: `0`.

## Вывод

Root cause был в нестабильном runtime-состоянии страницы оффера, а не только в DOM-селекторе submit. После фикса `leadsu` имеет второй recovery-контур: `reload` -> повторный `goto(target_url)`.

## Следующий шаг

- если ошибка повторится, первым делом смотреть debug HTML/PNG;
- если снова сохраняется пустой DOM, проверять:
  - сетевой contour/прокси;
  - партнёрский anti-bot;
  - final URL после `goto`;
  - наличие формы в `page.content()` до и после recovery.
