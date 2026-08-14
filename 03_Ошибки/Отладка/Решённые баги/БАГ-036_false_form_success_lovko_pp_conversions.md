# БАГ-036: ложное "успешно заполнен" без реальной конверсии ПП

## Симптом

- В логах Autolead отображалось `Оффер ... успешно заполнен`, но в партнёрской сети появлялась только малая часть конверсий.
- Практический пример: пользователь видел примерно `47` заполненных анкет, а в ПП отображалось около `3`.
- После ложного успеха контакт попадал в `autolead_send_history` как `sent`, поэтому следующий запуск пропускал его как уже отправленный.

## Зона системы

- `modules/vbiv_bot.py` — orchestration заполнения офферов и запись `send_history`.
- `modules/platforms/base.py` — общий `_wait_success()` для подтверждения отправки формы.
- `modules/platforms/lovko.py` — Lovko/Samokat/Ozon/Onecta-specific success detection.
- PostgreSQL runtime table `autolead_send_history`.
- ПП-интеграции: `traffic_hub/api/routers/postbacks.py`, `traffic_hub/api/routers/integrations.py`.

## Гипотеза

Бот помечал анкету как отправленную по слабому признаку: сам факт редиректа после submit/tracking считался успехом, хотя редирект мог быть обычным переходом на landing без принятия формы.

## Проверка

- Code fact:
  - `modules/platforms/base.py::_wait_success()` до фикса возвращал `ok`, если `current_url != url_before`.
  - `modules/platforms/lovko.py::_wait_samokat_success()` до фикса тоже возвращал `ok` на любом изменении URL.
  - `modules/vbiv_bot.py` после `FillResult.ok()` сразу вызывал `add_send_history(... status='sent')`.
- Runtime fact:
  - за последние 7 дней в `autolead_send_history` были сотни свежих `sent` по `Ozon`, `Onecta #2`, `Я еда`;
  - за тот же период оплаченных ПП-конверсий было существенно меньше;
  - в live БД были `Conversion` с `revenue > 0`, но статусом не `approved`.

## Наблюдение

- Редирект `tracking -> landing` не является доказательством принятой анкеты.
- Для ПП-метрик `payout > 0` является финансовым источником истины: даже если raw status сети пришёл как `rejected`, событие нужно считать оплаченной конверсией TrafficHub.
- Прямой postback раньше обновлял Google Sheets через глобальный `load_config()`, а не через owner-scoped конфиг интеграции.

## Вывод

Первичная причина расхождения `заполнено` vs `конверсии ПП` — ложноположительный success detection на форме. Вторичная причина — неверная классификация оплаченных ПП-событий и owner-scope риск при postback sheet sync.

## Исправление

- Product commit: `39e72fa2b fix: require explicit form success before marking sent`.
- `modules/platforms/base.py`:
  - обычный редирект больше не считается успехом;
  - success по URL разрешён только для явных маркеров `success/thanks/submitted/confirmed`;
  - убран слишком широкий success marker `ok`.
- `modules/platforms/lovko.py`:
  - Samokat/Lovko URL change больше не считается success без явного success URL/modal/body marker.
- `traffic_hub/api/routers/postbacks.py`:
  - `payout > 0` теперь классифицируется как `ConversionStatus.approved`;
  - обновление pending/processed Sheets при postback идёт через `bind_current_username(owner_username)` и owner-scoped `load_config(force_reload=True)`.
- Live DB:
  - backfill: старые `conversions` с `revenue > 0` переведены в `approved`;
  - создано 7 недостающих `financial_records`;
  - очищено 598 подозрительных свежих `sent` из `autolead_send_history` по Lovko-офферам `Ozon`, `Onecta #2`, `Я еда`, чтобы они могли пройти заново уже со строгой проверкой.

Дополнительное ужесточение после повторного расхождения `sent` vs конверсии ПП:

- Product commit: `190abe7b3 fix: require explicit lovko form confirmation`.
- Причина: после удаления правила `redirect = success` стандартный Lovko/Ozon/Onecta path всё ещё мог считать success по общему body/content, generic modal и видимой `[data-fancybox-close]`. Эти признаки не доказывают, что партнёрка приняла анкету.
- `modules/platforms/lovko.py::_wait_lovko_success()` теперь принимает успех только по явному `.thanks-modal`/dialog с новым success text или alert/dialog success. Пустой popup-shell и общий текст страницы больше не создают `send_history=sent`.
- Регрессия закрыта тестом `tests/test_lovko_success_detection.py`.

Дополнительная защита от неправильного IP при заполнении:

- Product commits:
  - `e33d9d85e fix: require ru form proxy for autofill`;
  - `3405b58d7 fix: avoid escaped fallback in proxy guard`.
- Причина: пользователь указал, что офферы плохо отрабатываются через немецкий IP; наличие proxy в настройках само по себе не доказывает, что Chromium реально выходит через RU.
- `modules/vbiv_bot.py::run_campaign()` перед формами выполняет browser-based RU preflight через настроенный `form_proxy`.
- `_verify_ru_form_proxy_or_raise()` открывает geo endpoint именно в Playwright page и требует `countryCode == RU`.
- Если proxy включён, но не распознан, или browser egress не RU, цикл заполнения останавливается до submit и не пишет `send_history=sent`.
- `Самокат` этим guard не выключается и не удаляется; его `disabled.html` остаётся отдельной проблемой оффера/лендинга.
- Регрессия закрыта `tests/test_proxy_config.py`.

## Проверка

- `python3 -m pytest -q` на live repo: `433 passed, 43 skipped`.
- Для `190abe7b3`: `python3 -m pytest -q` на live repo: `439 passed, 43 skipped`.
- Для RU form proxy guard: `python3 -m pytest -q` на live repo: `461 passed, 43 skipped`.
- Live deploy для `3405b58d7`: `docker compose up -d --build autolead_bot worker`; `/api/health` ok; `traffichub_app` и `traffichub_worker` healthy; container smoke для admin form proxy показал `217.29.62.68`, `RU`, `Moscow`.
- GitHub Actions для `39e72fa2b`: `CI` success, `Build and Push Docker Image` success.
- GitHub Actions для `190abe7b3`: `CI` success, `Build and Push Docker Image` success.
- Live deploy:
  - `docker compose up -d --build autolead_bot worker`;
  - `/api/health` вернул `{"status":"ok","version":"1.2","app":"TrafficHub"}`;
  - `traffichub_app` и `traffichub_worker` healthy.

## Следующий шаг

- При повторном проявлении сравнивать три источника:
  - `autolead_send_history` по owner/offer/date;
  - `conversions`/`postback_logs` по owner/date/revenue;
  - debug screenshots/html по конкретному офферу.
- Не возвращать правило “редирект = success” без отдельного теста и live-доказательства для конкретного лендинга.
