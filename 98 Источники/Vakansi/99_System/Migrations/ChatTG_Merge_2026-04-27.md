# Миграция базы ChatTG в единый vault

> **Дата**: 2026-04-27
> **Статус**: Завершено
> **Источник**: `C:\Users\Арт\Desktop\ChatTG`
> **Целевой vault**: `C:\Users\Арт\Desktop\Vakansi`

## Решение
Единым Obsidian vault принят `Vakansi`. База `ChatTG` не ведется отдельно: ее структура, чаты и знания считаются встроенными в общую систему `Vakansi`.

## Что проверено
- Папки `ChatTG\Active_Chats` и `Vakansi\01_Operations\Active_Chats` совпадают по составу.
- Папки `ChatTG\Knowledge_Base` и `Vakansi\01_Operations\Knowledge_Base` совпадают по составу.
- Экспорты `ChatTG\karina` и `Vakansi\01_Operations\Exports\karina` совпадают по составу.
- Экспорты `ChatTG\Kristina` и `Vakansi\01_Operations\Exports\Kristina` совпадают по составу.
- Шаблон `ChatTG\Templates\Chat_Template.md` уже присутствует в `Vakansi\99_System\Templates\Chat_Template.md`.
- Файл `ChatTG\Audit_Results.md` уже представлен в `Vakansi\03_Management\Audit_Results.md`.

## Карта соответствий
- `ChatTG\Active_Chats` -> `[[01_Operations/Active_Chats/]]`
- `ChatTG\Knowledge_Base\Scripts.md` -> `[[01_Operations/Knowledge_Base/Scripts]]`
- `ChatTG\Knowledge_Base\Objections.md` -> `[[01_Operations/Knowledge_Base/Objections]]`
- `ChatTG\Templates\Chat_Template.md` -> `[[99_System/Templates/Chat_Template]]`
- `ChatTG\Audit_Results.md` -> `[[03_Management/Audit_Results]]`
- `ChatTG\karina` -> `[[01_Operations/Exports/karina/export_results]]`
- `ChatTG\Kristina` -> `[[01_Operations/Exports/Kristina/export_results]]`

## Что оставлено за пределами миграции
- `.obsidian` из `ChatTG` не переносится: рабочей конфигурацией vault остается `.obsidian` из `Vakansi`.
- Пустые и служебные файлы старой базы вроде `2026-04-20.md`, `[[Objections]].md` и `Без названия.canvas` не импортируются в основной контур.

## Новое базовое правило
Если появляется новая база переписок или экспортов, она не живет отдельным vault. Все новые чаты, шаблоны, разборы и выгрузки сразу складываются в структуру `Vakansi`.
