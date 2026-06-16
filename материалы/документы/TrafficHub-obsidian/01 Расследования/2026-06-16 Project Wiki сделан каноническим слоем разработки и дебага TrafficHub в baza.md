# 2026-06-16 Project Wiki сделан каноническим слоем разработки и дебага TrafficHub в baza

## Симптом

- пользователь попросил не просто создать новый каркас `Project Wiki`, а органично добавить в него подходящие заметки;
- цель — сделать `baza` каноничной wiki для разработки и дебага `TrafficHub`.

## Зона системы

- внешний repo `baza`;
- Obsidian taxonomy для `TrafficHub`;
- dev/debug knowledge-layer.

## Гипотеза

`baza` можно сделать каноничной именно как project-navigation layer для `TrafficHub`, если:

- главный вход будет через `Project Wiki`;
- в `Project Wiki` попадут подтверждённые architectural/runtime/debug/API/DB-invariants;
- старый `01 Проекты/ТрафикХаб` останется evidence/source-layer, а не конкурентной точкой входа.

## Проверка

Подтверждено локально `2026-06-16` в живом clone `C:\Users\sergk\OneDrive\Desktop\Project\_tmp_baza_repo`:

- создан `Project Wiki/README.md` как новый канонический вход;
- `Index.md` обновлён и теперь ведёт на `[[README]]`;
- `01 Проекты/ТрафикХаб/README.md` обновлён:
  - он больше не основной вход;
  - он помечен как source-layer;
- в `Project Wiki` добавлены и заполнены подтверждённые разделы:
  - `00_Дашборд`
  - `01_Архитектура`
  - `02_Кодовая база`
  - `03_Отладка`
  - `05_AI_Контекст`
  - `06_Runtime`
  - `07_База данных`
  - `08_API`
- содержимое заполнено по подтверждённым заметкам:
  - `Контур проекта`
  - `Точки входа`
  - `Рантайм и хранилище`
  - `Сервисы и контейнеры`
  - `Данные и ownership`
  - `Очереди, worker и realtime`
  - `Auth и Access`
  - `Control Store`
  - `Google Sheets`
  - `Job Queue`
  - `Хранилища и runtime артефакты`
  - `Jobs и Worker`

## Наблюдение

- новый `Project Wiki` теперь даёт нормальный маршрут именно для разработки и дебага:
  - dashboard
  - architecture
  - code entrypoints
  - runtime
  - db
  - api
  - debugging
- `baza` всё ещё остаётся смешанным vault с диалогами, обучением и вакансиями;
- но для `TrafficHub` эти разделы больше не обязаны быть первым слоем навигации;
- то есть каноничность достигнута не через удаление остального vault, а через явный новый dev/debug entrypoint.

## Вывод

- `baza` приведён к состоянию, где он может служить каноничной project-wiki для разработки и дебага `TrafficHub`;
- канон в рамках `baza` теперь должен читаться так:
  - `Project Wiki` — главный вход
  - `01 Проекты/ТрафикХаб` — source-layer
  - остальные корни — auxiliary/legacy knowledge
- полный engineering source of truth по live runtime всё равно остаётся:
  - live `/root/TrafficHub`
  - локальная инженерная wiki `TrafficHub-obsidian`

## Следующий шаг

- запушить изменения `baza` в `origin/main`, если пользователь этого хочет;
- затем синхронизировать локальный mirror `wiki/Baza-obsidian` с новым каноническим `Project Wiki`;
- после этого поэтапно переносить часть legacy-заметок в новые разделы без массового blind move.
