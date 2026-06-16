# 2026-06-16 Полный архив TrafficHub-obsidian импортирован в baza

## Симптом

- `baza` уже содержала новый канонический `Project Wiki`;
- но полный инженерный архив `TrafficHub-obsidian` всё ещё жил отдельно и не был физически перенесён в `baza`.

## Зона системы

- внешний knowledge repo `baza`;
- локальная инженерная wiki `TrafficHub-obsidian`;
- sync-цепочка между кратким каноном и evidence layer.

## Гипотеза

Если импортировать весь `TrafficHub-obsidian` в `baza` как отдельный архивный слой и связать его ссылками с `Project Wiki`, то:

- `baza` станет самодостаточной базой знаний под Obsidian;
- старые расследования, ADR и playbooks не потеряются;
- краткий канон не придётся раздувать до размеров полного инженерного архива.

## Проверка

Подтверждено локально `2026-06-16`:

- весь каталог `wiki/TrafficHub-obsidian` импортирован в:
  - `baza/Project Wiki/raw/docs/TrafficHub-obsidian`
- в imported archive сохранены разделы:
  - `01 Расследования`
  - `02 Архитектура`
  - `03 Плейбуки`
  - `04 Сущности`
  - `05 Решения`
  - legacy-слой `01-Architecture`, `02-Modules`, `03-API`, `04-Database`, `05-Configuration`, `06-Deployment`, `07-Testing`, `08-DevLog`
- в `Project Wiki` добавлены bridge pages и ссылки:
  - `03_Отладка/Расследования TrafficHub`
  - `01_Архитектура/Архив архитектуры TrafficHub`
  - `06_Runtime/Плейбуки TrafficHub`
  - `05_AI_Контекст/Решения TrafficHub`
  - deep-link sections в `Внутреннее API`, `Внешнее API`, `Таблицы`, `Целостность данных`, `Воркеры`, `Архитектурные решения`
- изменения в `baza` закоммичены:
  - `1382f09`
  - `docs: import full TrafficHub obsidian archive`
- commit запушен в `origin/main`;
- локальный mirror `wiki/Baza-obsidian` после этого пересинхронизирован из live clone `baza`.

## Наблюдение

- `baza` теперь содержит оба слоя:
  - краткий канонический `Project Wiki`
  - полный imported archive `TrafficHub-obsidian`
- это лучше, чем пытаться переписать 100+ заметок вручную в новый шаблон;
- старая инженерная wiki не нужна как отдельная точка входа для чтения, но остаётся локальным рабочим origin для синхронизации.

## Вывод

- задача "перенести всё из `TrafficHub-obsidian` в `baza`" выполнена без потери содержимого;
- `baza` можно считать внешней самодостаточной базой знаний `TrafficHub`:
  - для быстрого входа использовать `Project Wiki`;
  - для глубоких расследований и доказательной базы использовать `Project Wiki/raw/docs/TrafficHub-obsidian`.

## Следующий шаг

- дальше переносить в верхний канон только high-signal факты, которые сокращают путь до дебага;
- legacy-архив не переписывать без причины, а использовать как evidence layer;
- при новых расследованиях сначала обновлять live code/runtime, потом `TrafficHub-obsidian`, потом краткий слой в `baza`.
