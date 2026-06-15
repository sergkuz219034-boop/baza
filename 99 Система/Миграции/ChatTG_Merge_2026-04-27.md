# Миграция базы ChatTG в единый vault

> Обновление 2026-06-15: текущая активная структура базы больше не использует пути `старый блок операций`, `старый блок управления`, `tasks` и `Wiki` в корне. Эти старые корни перенесены в `08 Архив/Legacy`, а рабочие материалы разложены по `02 Работа`, `06 План`, `07 Диалоги` и `99 Вакансии`.

> **Дата**: 2026-04-27
> **Статус**: Завершено
> **Источник**: `C:\Users\Арт\Desktop\ChatTG`
> **Целевой vault**: `C:\Users\Арт\Desktop\Vakansi`

## Решение
Единым Obsidian vault принят `Vakansi`. База `ChatTG` не ведется отдельно: ее структура, чаты и знания считаются встроенными в общую систему `Vakansi`.

## Что проверено
- Папки `ChatTG\Active_Chats` и `Vakansi\старый блок операций\Active_Chats` совпадают по составу.
- Папки `ChatTG\Knowledge_Base` и `Vakansi\старый блок операций\Knowledge_Base` совпадают по составу.
- Экспорты `ChatTG\karina` и `Vakansi\старый блок операций\Exports\karina` совпадают по составу.
- Экспорты `ChatTG\Kristina` и `Vakansi\старый блок операций\Exports\Kristina` совпадают по составу.
- Шаблон `ChatTG\Templates\Chat_Template.md` уже присутствует в `Vakansi\99_System\Templates\Chat_Template.md`.
- Файл `ChatTG\Audit_Results.md` уже представлен в `Vakansi\старый блок управления\Audit_Results.md`.

## Карта соответствий
- `ChatTG\Active_Chats` -> `[[07 Диалоги/Активные чаты/Example_Candidate_01]]`
- `ChatTG\Knowledge_Base\Scripts.md` -> `[[02 Работа/База знаний/Scripts]]`
- `ChatTG\Knowledge_Base\Objections.md` -> `[[02 Работа/База знаний/Objections]]`
- `ChatTG\Templates\Chat_Template.md` -> `[[07 Диалоги/Chat_Template]]`
- `ChatTG\Audit_Results.md` -> `[[02 Работа/Audit_Results]]`
- `ChatTG\karina` -> `[[08 Архив/Экспорты/ChatTG_karina]]`
- `ChatTG\Kristina` -> `[[08 Архив/Экспорты/ChatTG_Kristina]]`

## Что оставлено за пределами миграции
- `.obsidian` из `ChatTG` не переносится: рабочей конфигурацией vault остается `.obsidian` из `Vakansi`.
- Пустые и служебные файлы старой базы вроде `2026-04-20.md`, `[[Objections]].md` и `Без названия.canvas` не импортируются в основной контур.

## Новое базовое правило
Если появляется новая база переписок или экспортов, она не живет отдельным vault. Все новые чаты, шаблоны, разборы и выгрузки сразу складываются в структуру `Vakansi`.
