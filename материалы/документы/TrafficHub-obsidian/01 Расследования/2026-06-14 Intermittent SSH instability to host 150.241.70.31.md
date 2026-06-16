# 2026-06-14 Intermittent SSH instability to host 150.241.70.31

## Симптом

- Во время server-side аудита и чтения документации SSH-сессии к `150.241.70.31` периодически рвались ещё до нормальной интеракции.
- Подтверждённые сообщения:
  - `Connection timed out during banner exchange`
  - `Connection to 150.241.70.31 port 22 timed out`
  - `Connection closed by 150.241.70.31 port 22`

## Зона системы

- Host-level SSH access
- Не относится напрямую к:
  - `codex` SSH key
  - TrafficHub application code
  - Docker worker runtime

## Гипотеза

- Это не ошибка ключа и не отказ аутентификации.
- Вероятнее:
  - перегрузка host;
  - нестабильность SSH daemon / network path;
  - временный отказ banner exchange на уровне ssh transport.

## Проверка

- До появления симптома server-side команды уже успешно работали тем же `codex` ключом.
- Ошибка была непостоянной:
  - часть SSH-команд проходила;
  - часть обрывалась на banner exchange / closed connection.
- В тот же период на сервере был подтверждён высокий host load:
  - `2 vCPU`
  - высокий `load average`
  - заполненный swap

## Наблюдение

- Симптом похож на host/runtime instability, а не на неверный путь к ключу в wiki.
- При таком состоянии unsafe запускать длинные или рискованные server-side операции как будто проблема только в приложении.

## Вывод

- SSH instability 2026-06-14 считать отдельным runtime-фактором расследований.
- При повторении нельзя автоматически делать вывод:
  - `сломался codex user`
  - `ключ устарел`
  - `wiki/server-ssh-access.md неверен`

## Следующий шаг

- При повторном симптоме:
  1. сначала перепроверять коротким `ssh ... "echo ok"`;
  2. потом сверять host load и uptime;
  3. только после этого переходить к тяжёлым server-side действиям.
