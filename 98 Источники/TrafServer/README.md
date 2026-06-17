# TrafServer Workspace

Этот workspace не является канонической базой знаний.

Каноническая база теперь одна:

- [baza](C:/Users/Арт/Desktop/bazaGIT/baza)

Назначение `TrafServer`:

- source workspace для дебага и исследований TrafficHub;
- SSH-ключи и server-side утилиты;
- read-only server mirrors и snapshots;
- документы, плейбуки и промежуточные решения, которые ещё не перенесены в `baza`.

Главное правило:

- код TrafficHub **не хранится локально как git-clone**;
- рабочий mutable-репозиторий живёт только на сервере: `/root/TrafficHub`;
- GitHub используется как удалённая история и backup;
- каноническая wiki живёт в `baza`;
- `TrafServer` используется только как source workspace для исследований и промежуточных материалов.

## Что должно лежать в этой папке

Разрешённый состав `C:\Users\Арт\Desktop\TrafServer`:

- `.obsidian/`
- `01 Расследования/`
- `02 Архитектура/`
- `03 Плейбуки/`
- `04 Сущности/`
- `05 Решения/`
- `.ssh/`
- `tools/`
- `docs/`
- `150.241.70.31/`
- `remote_files/`
- `remote_server_snapshot/`
- локальные SSH/remote helper scripts в `tools/`

Допустимые локальные артефакты:

- read-only зеркала server code;
- server snapshots;
- redacted диагностические документы.

## Что не должно лежать в этой папке

Запрещено держать внутри workspace:

- `.git` и любые локальные git-клоны TrafficHub;
- полноценные app source trees;
- build-output и unpack runtime;
- локальные SQLite/runtime state файлы приложения;
- временные `.bak_*` и vendor/runtime directories;
- постоянные рабочие копии GitHub-репозитория.

Если для задачи временно появляется локальный source tree, он должен быть одноразовым и удаляться после завершения задачи.

## Где теперь лежат вынесенные runtime/state файлы

Техническое хранилище вне vault:

- `C:\Users\Арт\Desktop\TrafServer_storage`
- `C:\Users\Арт\Desktop\TrafServer_runtime`

Туда вынесены:

- локальные БД и state-файлы;
- runtime secrets / временные unpack-папки;
- вспомогательные vendor/runtime каталоги, которые мешают Obsidian.

## Канонический контур изменения кода

Все изменения TrafficHub выполняются так:

1. подключение к серверу;
2. работа в `/root/TrafficHub`;
3. чтение, правки и проверки там;
4. commit в серверном repo;
5. push с сервера на GitHub;
6. синхронное обновление wiki в локальном `TrafServer`.

Локальный clone `TrafficHub-github` больше не используется и не должен создаваться повторно.

## Источники истины

- live runtime и контейнеры на сервере;
- серверный репозиторий `/root/TrafficHub`;
- GitHub-репозиторий как удалённая история;
- локальная wiki как инженерная карта.

Старые заметки, частичные snapshots и зеркала кода не считаются каноном без сверки с сервером.

## Полезные входные точки

- [Index.md](C:/Users/Арт/Desktop/TrafServer/Index.md)
- [docs/README.md](C:/Users/Арт/Desktop/TrafServer/docs/README.md)
- [remote_files/README.md](C:/Users/Арт/Desktop/TrafServer/remote_files/README.md)
- [remote_server_snapshot/README.md](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/README.md)
- [tools/README.md](C:/Users/Арт/Desktop/TrafServer/tools/README.md)
- [tools/local_ssh.py](C:/Users/Арт/Desktop/TrafServer/tools/local_ssh.py)
- [tools/remote_exec.py](C:/Users/Арт/Desktop/TrafServer/tools/remote_exec.py)
- [tools/ssh_key_readiness.py](C:/Users/Арт/Desktop/TrafServer/tools/ssh_key_readiness.py)
- [tools/prepare_ssh_migration.ps1](C:/Users/Арт/Desktop/TrafServer/tools/prepare_ssh_migration.ps1)
- [03 Плейбуки/Debugging.md](C:/Users/Арт/Desktop/TrafServer/03%20Плейбуки/Debugging.md)
- [03 Плейбуки/Documentation synchronization contract.md](C:/Users/Арт/Desktop/TrafServer/03%20Плейбуки/Documentation%20synchronization%20contract.md)
- [03 Плейбуки/Server-only development.md](C:/Users/Арт/Desktop/TrafServer/03%20Плейбуки/Server-only%20development.md)
- [03 Плейбуки/Server repo push to GitHub.md](C:/Users/Арт/Desktop/TrafServer/03%20Плейбуки/Server%20repo%20push%20to%20GitHub.md)
- [01 Расследования/README.md](C:/Users/Арт/Desktop/TrafServer/01%20Расследования/README.md)
- [02 Архитектура/README.md](C:/Users/Арт/Desktop/TrafServer/02%20Архитектура/README.md)
- [03 Плейбуки/README.md](C:/Users/Арт/Desktop/TrafServer/03%20Плейбуки/README.md)
- [04 Сущности/README.md](C:/Users/Арт/Desktop/TrafServer/04%20Сущности/README.md)
- [05 Решения/README.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/README.md)

## Короткий статус после миграции

- локальный clone TrafficHub удалён;
- Obsidian vault очищен от проблемных runtime-папок;
- helper-утилиты вынесены из корня в `tools/`;
- каноническая база сведена в `baza`;
- дальнейшая работа с кодом должна идти только через серверный repo.
