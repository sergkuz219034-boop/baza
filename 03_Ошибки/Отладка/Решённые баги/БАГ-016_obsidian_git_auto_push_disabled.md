# БАГ-016: Obsidian Git не отправлял изменения на GitHub автоматически

## Симптом

Правки в Obsidian сохранялись локально, но не появлялись в удалённом репозитории без ручного запуска push.

## Зона системы

- vault `baza`
- `.obsidian/plugins/obsidian-git/data.json`
- плагин Obsidian Git

## Гипотеза

Автокоммит мог срабатывать, но автопуш был выключен или не дожидался завершения редактирования.

## Проверка

- в `data.json` было:
  - `autoPushInterval: 1`
  - `autoPullInterval: 5`
  - `autoPullOnBoot: true`
  - `autoBackupAfterFileChange: true`
  - `differentIntervalCommitAndPush: true`
- код плагина в `main.js` показывает:
  - `autoPushInterval > 0` нужен для запуска авто-пуша;
  - `autoBackupAfterFileChange` управляет режимом "после остановки правок".

## Наблюдение

При текущем конфиге плагин пытался делать pull на старте и по таймеру, пока в открытой заметке были локальные изменения. Из-за этого pull падал с merge-конфликтом и блокировал дальнейшую синхронизацию.

## Вывод

Причина была в конфигурации, а не в GitHub и не в репозитории.

Исправление в актуальном `main`:

- `autoPushInterval` -> `1`
- `autoPullInterval` -> `0`
- `autoPullOnBoot` -> `false`
- `autoBackupAfterFileChange` -> `true`

## Следующий шаг

- Проверить в Obsidian, что после правки файла через несколько минут появляется новый commit и затем push в `main`.
- Если автосинхронизация всё ещё не срабатывает, проверить `Git is ready`, upstream branch и доступ к remote.
