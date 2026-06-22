# Fast debug loop operating model

## Проблема

Текущий workflow технически правильный, но для частых багов он слишком длинный: много ручных переключений, слишком широкий scope проверки и поздний wiki-sync.

## Контекст

У нас уже есть обязательные контуры:

- серверный mutable repo `/root/TrafficHub`;
- локальный `TrafServer` как workspace/wiki;
- GitHub как история;
- live runtime как источник истины для server-only или container-only симптомов.

Но без сокращённого цикла дебаг начинает терять скорость на повторяющихся инцидентах.

## Решение

Принять short-loop operating model:

- один симптом;
- одна зона системы;
- одна минимальная правка;
- один targeted test или live smoke;
- один container restart только если он реально нужен;
- немедленный commit/push;
- немедленный wiki-sync.

## Последствия

- меньше лишних чтений и широких прогонов;
- быстрее локализуются regression-петли;
- проще держать wiki в актуальном состоянии;
- уменьшается риск “починили одно, сломали другое” за счёт малого scope правки.

## Альтернативы

- Сохранять текущий широкий workflow для всех задач.
- Держать отдельный staging clone локально.
- Делать сначала код, а wiki и push откладывать до конца серии задач.

Эти альтернативы проигрывают по скорости и плохо подходят для текущего режима server-first development.

## Вывод

Для TrafServer/TrafficHub оптимален не “большой” процесс разработки, а короткий deterministic loop: inspect -> patch -> verify -> commit -> sync.

## Связанные заметки

- [[Fast debug loop]]
- [[Server-only development]]
- [[Documentation Synchronization Contract]]
