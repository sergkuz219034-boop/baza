# 2026-07-03 Zarplata full resume contacts

## Симптом

У `admin` Зарплата.ру в полном цикле показывала `отклики > 0`, но `найдено резюме 0` и `в Sheets добавлено 0`.

## Зона системы

- `modules/zarplata_api.py`
- `services/leads_service.py`
- runtime job `zarplata` / `run`
- admin Google Sheets: pending table `1seCE2MPKZV01LJMvL4CuvSDL7IdG-V_vN6hmqoAcZOs`

## Гипотеза

Импорт читает короткий объект `item.resume` из `/negotiations`, но контакты Зарплата.ру отдаёт только в полном резюме по `resume.url`.

## Проверка

Live sample через `ZarplataClient`:

- `/negotiations/...` возвращает `item.resume`;
- в коротком `resume` есть `can_view_full_info=True`, `contact_view_status=FULL`, но нет телефона/почты;
- `GET resume.url` возвращает полный объект с `contact`;
- `_extract_contacts(full_resume)` извлекает телефон.

## Наблюдение

До фикса нормализация отбрасывала такие строки как contactless:

- короткий `item.resume` без `contact`;
- `_has_contact(lead) == False`;
- результат: `response_loaded` большой, `normalized/uploaded` ноль.

## Вывод

Для Зарплата.ру отклики из negotiations нельзя выгружать по краткому объекту резюме. Нужно догружать full resume по API URL, иначе лиды с доступными контактами теряются.

## Исправление

В `modules/zarplata_api.py`:

- добавлена догрузка full resume через `resume.url`;
- добавлен cache full resume URL, чтобы не ходить повторно по одному URL;
- при включённых negotiations отключён лишний default-проход `only_in_responses`, потому что он не даёт контакты и замедляет импорт;
- добавлен regression test на сценарий: negotiation содержит short resume, contact появляется только после full resume fetch.

Коммиты product repo:

- `dda20f735 fix: load zarplata contacts from full resumes`
- `7853ad504 fix: streamline zarplata negotiation import`

## Runtime-проверка

Admin live check:

- Rabota.ru full cycle: `Итого лидов: 104`, `Пропущено: 45`, `В Sheets добавлено строк: 59`;
- Зарплата.ру после фикса: pending table выросла с `9506` до `9963` data rows;
- прирост таблицы: `+457` строк;
- повторный запуск Зарплата.ру увидел уже добавленные строки как дубли: `Пропущено (уже есть в Google Sheets): 493`.

## Следующий шаг

Улучшить итоговый лог Зарплата.ру: если job прерван после upload или контейнер пересобран, в логах может отсутствовать финальная строка `в Sheets добавлено`, хотя строки уже добавлены. Нужен atomic run summary в БД для standalone `zarplata` job.
