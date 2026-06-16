# 2026-06-16 GitHub access path к baza задокументирован, но не воспроизведён новыми токенами

## Симптом

- пользователь прислал несколько GitHub token для доступа к `sergkuz219034-boop/baza`;
- все новые токены в текущей сессии дают `401 Unauthorized`;
- при этом в wiki уже есть заметка, что в этот же день sync `baza` был успешно восстановлен.

## Зона системы

- GitHub access path;
- внешний repo `baza`;
- локальная wiki и локальный mirror `Baza-obsidian`.

## Гипотеза

Ранее рабочий доступ к `baza` действительно был получен, а текущая невоспроизводимость вызвана не самим PAT, а способом, которым токен подставлялся в shell-проверки этой сессии.

## Проверка

Подтверждено локально `2026-06-16`:

- `wiki/TrafficHub-obsidian/01 Расследования/2026-06-16 Внешний sync с GitHub репозиторием baza восстановлен.md` фиксирует такой путь:
  - `GET https://api.github.com/user` новым токеном -> `200`
  - `GET https://api.github.com/repos/sergkuz219034-boop/baza` -> `200`
  - `git clone https://sergkuz219034-boop:<token>@github.com/sergkuz219034-boop/baza.git` -> успешно
- `wiki/Baza-obsidian/99 Система/Obsidian_Git_Setup.md` дополнительно фиксирует рабочую модель для людей:
  - клон `sergkuz219034-boop/baza`
  - открыть клон как Obsidian vault
  - дальше синхронизация через `Obsidian Git: Commit-and-sync`
- `wiki/Baza-obsidian/.obsidian/plugins/obsidian-git/data.json` подтверждает, что vault настроен под Obsidian Git, но не хранит GitHub credentials;
- в shell-командах этой сессии строка `'<SECRET>'` не заменялась реальным токеном:
  - тест `'$token = ''<SECRET>''; $token.Length'` вернул `8`
  - значит предыдущие проверки реально уходили с буквальным значением `<SECRET>`
- после прямой подстановки реального PAT из пользовательского сообщения подтверждено:
  - `GET https://api.github.com/user` -> `200`, `login=sergkuz219034-boop`
  - `GET https://api.github.com/repos/sergkuz219034-boop/baza` -> `200`
  - `git clone https://sergkuz219034-boop:<token>@github.com/sergkuz219034-boop/baza.git` -> успешно

## Наблюдение

- wiki описывает конкретный исторический access path, а не абстрактную идею;
- этот путь состоит из двух частей:
  - проверка токена через GitHub API `Bearer`
  - clone по HTTPS с PAT в URL и owner `sergkuz219034-boop`
- documented path воспроизводится, если использовать реальный PAT, а не shell placeholder;
- локальный mirror `wiki/Baza-obsidian` и открытые в `.obsidian/workspace.json` файлы подтверждают, что с mirror действительно работали как с уже существующим vault.

## Вывод

- по wiki предыдущий успешный способ подключения к `baza` был:
  - GitHub API с PAT
  - затем `git clone` HTTPS URL репозитория
  - затем работа с клоном как с Obsidian vault
- текущая сессия подтвердила, что прошлые `401` были ложным следствием shell placeholder `<SECRET>`, а не признаком невалидного PAT;
- канон на сейчас:
  - структура и содержимое `baza` подтверждены по локальному mirror и по свежему `git clone`;
  - живой GitHub access path заново воспроизведён в этой сессии.

## Следующий шаг

- в будущих shell-проверках не использовать placeholder `<SECRET>` как будто он автоматически раскроется;
- если нужно проверить PAT внутри shell, подставлять реальное значение явно или использовать иной секретный канал передачи;
- для быстрого smoke-path достаточно:
  - `GET https://api.github.com/user`
  - `GET https://api.github.com/repos/sergkuz219034-boop/baza`
  - `git clone https://sergkuz219034-boop:<token>@github.com/sergkuz219034-boop/baza.git`
