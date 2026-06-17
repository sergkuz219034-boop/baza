# Obsidian vault scan EPERM

Дата: 2026-06-01
Симптом: Obsidian не открывает vault `C:\Users\Арт\Desktop\TrafServer` и падает на индексации с ошибкой:

`Error: EPERM: operation not permitted, scandir 'C:\Users\Арт\Desktop\TrafServer\tmp_paramiko\bcrypt'`

## Анализ

- Проблема воспроизводилась не на markdown-заметках, а на рекурсивном обходе служебных Python-runtime каталогов внутри vault.
- Ручная проверка показала, что Obsidian-совместимость ломали временные директории:
  - `tmp_paramiko`
  - `_sshdeps`
  - `_sshdeps_local`
  - `_sshdeps2`
  - `.codex-tmp`
- При полном обходе workspace PowerShell тоже получал множественные `Access denied` на вложенных каталогах вроде `bcrypt`, `cffi`, `paramiko`, что подтверждает root cause на уровне файловой структуры vault, а не содержимого заметок.

## Причина

- Описание проблемы: Obsidian индексировал runtime-каталоги с бинарными Python-зависимостями внутри vault.
- Первопричина: в markdown-хранилище лежали временные технические папки, не предназначенные для сканирования Obsidian.
- Критичность: `Medium`
- Последствия: vault не открывается; расследование и документация блокируются.
- Рекомендуемое исправление: вынести служебные runtime-каталоги за пределы vault и не хранить временные Python-окружения рядом с Obsidian-хранилищем.

## Исправление

Временные каталоги перенесены из:

- `C:\Users\Арт\Desktop\TrafServer`

в:

- `C:\Users\Арт\.codex\memories\TrafServer-runtime-cache`

После переноса повторный рекурсивный обход `C:\Users\Арт\Desktop\TrafServer` завершился с `SCAN_ERRORS=0`.

## Побочный эффект

- Локальные SSH-утилиты больше не могут неявно рассчитывать, что vendored runtime лежит внутри vault.
- Поэтому локальное SSH-tooling нужно привязывать к внешнему runtime явно или через helper.
