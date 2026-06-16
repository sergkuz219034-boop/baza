# Runtime restart-loop после rebuild был вызван missing import threading

## Симптом

- после rebuild `autolead_server_bot` ушёл в restart-loop;
- `traffichub_worker` при этом остался healthy.

## Зона системы

- `api/server.py`
- контейнер `autolead_server_bot`

## Гипотеза

- в startup/lifespan path есть обращение к модулю, который не импортирован на верхнем уровне.

## Проверка

- прочитан live `docker logs autolead_server_bot`;
- подтверждён traceback:
  - `File "/app/api/server.py", line 192, in _lifespan`
  - `job_bridge_stop = threading.Event()`
  - `NameError: name 'threading' is not defined`

## Наблюдение

- в `api/server.py` добавлен `import threading`;
- после rebuild/restart `autolead_server_bot` вернулся в `healthy`.

## Вывод

- это не регресс логики `Резюме`, а уже существующий runtime-дефект startup-path, который стал виден после пересборки образа.

## Следующий шаг

- при любых следующих rebuild/restart проверять оба контейнера:
  - `autolead_server_bot`
  - `traffichub_worker`
- перед заявлением о завершении server-side фикса всегда смотреть health и `docker logs`.
