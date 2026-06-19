# БАГ-025: live-контейнер не получил полный leadsu fix после GitHub push

## Симптом

После фикса `leadsu` пользователи продолжили видеть ошибку:

- `Ошибка Воксис [11]: leadsu: кнопка submit не найдена`
- `form-failure, retry queue пропущена`

Свежий debug-артефакт `debug_Воксис_20260619_222202.html` снова имел размер `39` байт и содержал пустой DOM.

## Зона системы

- deploy/runtime drift
- `/root/TrafficHub`
- image `traffichub-autolead_bot`
- container `/app/modules/platforms/leadsu.py`

## Гипотеза

Исправление было запушено в GitHub и частично лежало в host-repo, но не было полноценно доставлено в исполняемый container image. Поэтому пользователи продолжали работать на старом коде внутри `/app`.

## Проверка

Сравнение live runtime показало:

- GitHub `origin/main` уже был на `2042680f6`;
- server repo `/root/TrafficHub` всё ещё показывал `HEAD=59949a191`;
- host-файл `modules/platforms/leadsu.py` содержал marker `повторно открываю target_url`;
- container-файл `/app/modules/platforms/leadsu.py` сначала содержал только первую часть recovery `пустая страница перед submit, пробую reload`, но не содержал повторный `goto(target_url)`.

## Наблюдение

Root cause был не в новом DOM оффера, а в рассинхроне deploy-слоёв:

- GitHub был обновлён;
- host-файл был изменён;
- исполняемый container image оставался старым/частично старым.

Исправление:

- полный `leadsu.py` и `sheets_sync.py` сначала были доставлены в live containers аварийно;
- затем `autolead_bot` и `worker` были пересобраны через `docker compose build autolead_bot worker`;
- контейнеры были пересозданы через `docker compose up -d --no-deps autolead_bot worker`;
- server repo HEAD приведён к `2042680f6` через безопасный mixed reset индекса/HEAD до `origin/main`, без изменения чужих `AccountManager`-файлов.

## Runtime-проверка

После пересборки:

- marker `target_url = str((self.offer or {}).get("target_url")...)` есть внутри `/app/modules/platforms/leadsu.py`;
- marker `повторно открываю target_url` есть внутри `/app/modules/platforms/leadsu.py`;
- `docker exec autolead_server_bot pytest -q tests/test_leadsu_blank_recovery.py tests/test_sheets_queues.py` -> `29 passed`;
- runtime-probe `Воксис` на одном `admin` lead вернул `success=True`, `duplicate=True`.

## Вывод

Ошибка появилась не потому, что пользователи работали на финальном релизе и сам релиз внезапно сломался. Live-контейнер фактически не совпадал с уже исправленным GitHub/host-кодом. Канонический deploy для таких фиксов должен включать не только `git push`, но и проверку `/app` внутри контейнера после `docker compose up`.

## Следующий шаг

- после каждого live-fix проверять три уровня:
  - `git rev-parse HEAD` в `/root/TrafficHub`;
  - marker-код внутри `/app` контейнера;
  - тесты внутри свежесозданного контейнера;
- не считать GitHub push достаточным доказательством deploy.
