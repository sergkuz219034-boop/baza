# Autolead user settings и ownership

## Проблема

Пользовательские настройки и доступ к Autolead ломались на стыке ролей, ownership и скрытых UI-полей.

## Контекст

- `user` должен иметь свой независимый профиль;
- при этом не должен получать доступ к глобальным admin-only secrets;
- реальная поломка проявлялась так:
  - пользователь не видел нужные `Google Sheets` поля;
  - jobs могли восприниматься как “не работают”, хотя backend уже жил.

## Решение

- открыть `user` доступ к:
  - `google_sheets_pending_spreadsheet_id`
  - `google_sheets_processed_spreadsheet_id`
- оставить admin-only:
  - глобальные auth secrets
  - service account upload
  - системные/admin блоки
- дополнительно валидировать owner-scoped proxy config до сохранения и при runtime-чтении:
  - settings API отвергает невалидный `proxy_url`
  - browser-runner не пытается использовать нераспознанный proxy из user config

## Последствия

- `user` может сам конфигурировать свою выгрузку;
- ownership-конфиг становится ближе к реальному multi-user сценарию;
- регрессия покрыта тестом в `tests/test_auth_roles.py`.
- По live-коду `api/autolead_access.py` на `2026-06-11` сам access-gate больше не режет доступ по configured owner;
- следовательно owner-изоляцию нельзя описывать как “чужой user не войдёт в Autolead” без уточнения слоя:
  - settings/jobs/logs остаются owner-scoped;
  - но доступ к настроенному runtime сейчас определяется не owner-match, а фактом authenticated principal + runtime ready.
- На `2026-06-14` подтверждено ещё одно следствие owner-scoped модели:
  - сломанный `rabota_ru.proxy_url` у конкретного пользователя ломает только его runtime-path;
  - это не означает глобальную неисправность оффера или платформы.

## Альтернативы

- Скрыть `Google Sheets` полностью от `user`.
  - Приводит к неработающему профилю и нарушает модель “каждый user работает со своими лидами и значениями”.
- Доверять любому строковому `proxy_url`, пришедшему из runtime config.
  - Приводит к ложным багам уровня “оффер мёртв”, хотя реально сломан только user-scoped config.
