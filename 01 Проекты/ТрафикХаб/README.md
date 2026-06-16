# ТрафикХаб

Активный технический проект для сопровождения через серверный репозиторий и локальную wiki.

## Что внутри

- [[Контур проекта]] — что подтверждено по проекту и где его канонический код
- [[Точки входа]] — куда смотреть в первую очередь
- [[Рантайм и хранилище]] — что лежит в runtime и storage
- [[Правила работы]] — как безопасно менять проект и не строить ложную картину
- [[SSH и доступ]] — канонический вход на сервер и разница human/agent path
- [[Сервисы и контейнеры]] — live compose-контур и роли контейнеров
- [[Данные и ownership]] — PostgreSQL/control store, user-scoped Google Sheets и инварианты таблиц
- [[Очереди, worker и realtime]] — Redis queue, owner-scoped jobs, stop-path и UI-логи

## Быстрый вывод

- локальный workspace `C:\Users\sergk\OneDrive\Desktop\traffichubserver` не является git-клоном приложения;
- живой изменяемый репозиторий находится на сервере в `/root/TrafficHub`;
- текущая система не one-process: web, worker, PostgreSQL, Redis, auth/license, Account Manager и Caddy разделены по контейнерам;
- Google Sheets и job execution owner-scoped: нельзя переносить выводы между пользователями без проверки их собственных settings/runtime.
