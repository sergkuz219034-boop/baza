# Onecta 2 не видна в Lovko

## Симптом

TrafficHub сообщает об успешном заполнении `Onecta #2`, но в кабинете Lovko конверсии не видны.

## Зона системы

[[Интеграции]], owner-scoped `offer_mapping`, Playwright-отправка анкет, атрибуция Lovko.

## Гипотеза

Успешная отправка формы в браузере не превращается в подтвержденную конверсию Lovko либо статистика Lovko не синхронизируется обратно в TrafficHub.

## Проверка

- Проверен live PostgreSQL на сервере `150.241.70.31`.
- Проверены `control_user_app_configs`, `autolead_send_history`, `autolead_app_log` и `postback_logs`.
- Проверен HTTP redirect `https://tracking.lovko.pro/L6eTlM`.

## Наблюдение

- У `artem` `Onecta #2` включена и привязана к вакансиям `54309931`, `54257329`.
- TrafficHub зарегистрировал 9 отправок со статусом `sent` за 2026-06-24.
- В `postback_logs` нет конверсий `Onecta`.
- Одна ссылка `https://tracking.lovko.pro/L6eTlM` скопирована в конфиги `admin`, `alex`, `artem`, `kursmerkusheva@gmail.com`, `sergkuz2190`.
- Redirect этой ссылки содержит `pid=4144`, `offer_id=173` и уникальный `affise_click_id`.
- Владелец подтвердил, что `pid=4144` принадлежит профилю Artem. Гипотеза о чужой ссылке отклонена.
- Сообщение TrafficHub «анкета успешно заполнена» подтверждает UI-submit, но не подтверждает появление конверсии в Lovko.
- Для `artem` отсутствует строка Lovko в `network_integrations`, поэтому автоматической сверки со статистикой партнерки нет.
- Текущий `LovkoPlatform._wait_lovko_success()` считает успехом появление success-модального окна/текста в DOM. HTTP-ответ принимающего API и наличие конверсии в Lovko он не проверяет.
- Read-only вход в Lovko с owner-scoped credentials `artem` успешен, но кабинет возвращает `0` распознанных конверсий за доступный текущий период.
- Обнаружен и исправлен отдельный дефект `LovkoScraper.get_conversions()`: служебный bootstrap JSON со свойством `status` ошибочно принимался за конверсию. После строгой фильтрации ложная строка исчезла. Исправление: TrafficHub `3462e07ec`.

## Вывод

Подтверждено, что ссылка принадлежит Artem и click attribution создается. Кабинет Lovko не содержит распознанных конверсий за проверенный период. Неподтвержденный участок — переход от UI-submit лендинга Onecta к зарегистрированной конверсии Lovko. TrafficHub преждевременно называет DOM-success успешным заполнением.

## Следующий шаг

1. Выполнить один контролируемый тест и сохранить `affise_click_id`, запрос отправки формы и ответ API лендинга.
2. Сверить этот click ID и телефон с кабинетом Lovko, включая pending/rejected и фильтр дат.
3. Настроить owner-scoped Lovko credentials/sync для `artem`.
4. Разделить в модели статусы `form_submitted` и `conversion_confirmed`; не считать DOM-submit подтвержденной конверсией.
5. Для остальных пользователей использовать только персональные tracking URL владельцев их партнерских кабинетов.

Связано: [[2026-06-24 owner-scoped ссылки офферов]], [[2026-06-24 Onecta 2 для user profiles]].
