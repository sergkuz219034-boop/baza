# 2026-06-16 В Project Wiki добавлены dev-debug контракты TrafficHub

## Симптом

- после структурной перестройки `baza` канонический слой `Project Wiki` уже существовал;
- но ему не хватало части эксплуатационных контрактов, чтобы быть удобной wiki именно для разработки и дебага `TrafficHub`.

## Зона системы

- `baza` / `Project Wiki`;
- dev/debug navigation layer `TrafficHub`.

## Гипотеза

Если в `Project Wiki` добавить не абстрактные обзоры, а подтверждённые runtime/API/DB/debug-контракты, то для повседневной разработки и triage можно будет входить только через `baza`, не проваливаясь каждый раз в полный инженерный архив.

## Проверка

Подтверждено локально `2026-06-16`:

- в живом clone `baza` обновлены страницы:
  - `Project Wiki/03_Отладка/Известные проблемы.md`
  - `Project Wiki/06_Runtime/Анализ логов.md`
  - `Project Wiki/06_Runtime/Воркеры.md`
  - `Project Wiki/07_База данных/Таблицы.md`
  - `Project Wiki/07_База данных/Целостность данных.md`
  - `Project Wiki/08_API/Внутреннее API.md`
  - `Project Wiki/08_API/Внешнее API.md`
- добавлены подтверждённые контракты:
  - queue/status/UI triage
  - worker playbook
  - expected log/status events
  - control store как primary source
  - owner-scoped runtime data
  - access/session/websocket invariants
  - Account Manager JWT bridge
- изменения закоммичены и запушены в GitHub repo `baza`:
  - commit `ad3a7e2`
  - message `docs: enrich TrafficHub dev-debug canon`
- после этого локальный mirror `wiki/Baza-obsidian` пересинхронизирован с обновлённым repo.

## Наблюдение

- `Project Wiki` теперь содержит не только обзорную карту, но и практический dev/debug минимум;
- из `11_Операционный контур` почти не потребовалось перетаскивать содержимое в канон:
  - полезной оказалась в основном карта источников и границ канона;
- основной сигнал всё ещё идёт из:
  - live `/root/TrafficHub`
  - `TrafficHub-obsidian`
  - краткого project-layer в `baza`

## Вывод

- `baza` в текущем состоянии можно считать рабочей канонической wiki для входа в разработку и дебаг `TrafficHub`;
- полный инженерный канон не исчез, но теперь играет роль глубокой доказательной базы, а не обязательной первой точки входа.

## Следующий шаг

- дальше переносить только high-signal notes, если они реально уменьшают путь до локализации бага;
- не раздувать `Project Wiki` материалами по вакансиям, диалогам и общему обучению;
- поддерживать sync:
  - сначала live code/runtime
  - потом `TrafficHub-obsidian`
  - потом краткий слой `baza`.
