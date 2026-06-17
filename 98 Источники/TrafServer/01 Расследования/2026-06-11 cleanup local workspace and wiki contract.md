# 2026-06-11 cleanup local workspace and wiki contract

Теги: #debug #workspace #wiki

## Симптом

Локальный `TrafServer` снова начал обрастать helper-скриптами в корне, служебными runtime-артефактами и неявными правилами ведения wiki.

## Зона системы

- локальный Obsidian vault
- server-side helper utilities
- правила documentation synchronization

## Гипотеза

Если оставить корень vault как смешанный workspace без жёсткой структуры, он снова превратится в полу-репозиторий с мусором, а инженерные правила работы останутся только в чате и быстро потеряются.

## Проверка

- Проверена фактическая структура `C:\Users\Арт\Desktop\TrafServer`.
- Выделены лишние элементы в корне: helper-скрипты и отдельный ключевой файл.
- Проверены ссылки в `README.md` и wiki на старые пути.

## Наблюдение

- Корень vault можно оставить почти пустым: только каталоги wiki, `README.md`, `CHANGELOG.md`.
- Helper-утилиты безопасно живут в `tools/`.
- Для `tools/local_ssh.py` пришлось поправить вычисление корня workspace после переноса.
- У Obsidian и wiki не было постоянной страницы, фиксирующей жёсткий режим documentation synchronization.

## Вывод

Локальный workspace нужно держать в режиме:

- `TrafServer` = wiki + SSH + server utilities;
- runtime/state и одноразовые артефакты — вне vault;
- правила работы с документацией фиксируются отдельной постоянной заметкой, а не остаются только в переписке.

## Следующий шаг

Если в `TrafServer` снова появятся исходники приложения, build-output или временные runtime-каталоги, их нужно либо сразу выносить наружу, либо оформлять как одноразовые артефакты с понятным TTL.

## Связанные заметки

- [[Documentation synchronization contract]]
- [[Server-only development]]
- [[2026-06-11 local clones forbidden workspace policy]]
