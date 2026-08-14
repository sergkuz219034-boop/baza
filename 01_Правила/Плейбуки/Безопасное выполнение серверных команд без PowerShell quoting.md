# Безопасное выполнение серверных команд без PowerShell quoting

## Назначение

Канонический способ запускать команды на сервере TrafficHub из Windows workspace без ошибок PowerShell-экранирования.

## Проблема

Ручной запуск вида `ssh "... | grep ... $var ..."` через PowerShell ломается на:

- `|`
- `$`
- кавычках;
- heredoc;
- многострочных bash-командах;
- кириллице;
- вложенных `docker exec`, `grep`, `sed`, `python <<EOF`.

## Решение

Использовать `tools/remote_exec.py` или wrapper `tools/remote_bash.ps1`.

Они передают сложный bash на сервер как временный скрипт, а не как строку, которую PowerShell должен интерпретировать.

## Основной вариант

```powershell
@'
cd /root/TrafficHub
git status --short
docker ps --format "{{.Names}} {{.Status}}" | grep autolead
'@ | python C:\Users\Арт\Desktop\TrafServer\tools\remote_exec.py --stdin
```

## Короткая команда

```powershell
C:\Users\Арт\Desktop\TrafServer\tools\remote_bash.ps1 -Cwd /root/TrafficHub -Command "git status --short"
```

## Скрипт из файла

```powershell
python C:\Users\Арт\Desktop\TrafServer\tools\remote_exec.py --file C:\path\to\script.sh
```

## Правило

Для любой команды сложнее одного простого `git status` использовать STDIN-вариант.

Не писать вручную:

```powershell
ssh user@host "cd /root/TrafficHub && grep 'x|y' file && python3 - <<'PY'"
```

## Подтверждение

Проверено на кейсах:

- кириллица;
- pipe `|`;
- `$` внутри удалённого bash;
- одинарные/двойные кавычки;
- heredoc Python;
- работа из `/root/TrafficHub`.

## Связанные сущности

- [[Remote ops tools]]
