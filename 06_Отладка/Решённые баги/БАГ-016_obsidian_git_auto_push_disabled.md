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
  - `autoPushInterval: 0`
  - `autoBackupAfterFileChange: false`
  - `differentIntervalCommitAndPush: true`
- код плагина в `main.js` показывает:
  - `autoPushInterval > 0` нужен для запуска авто-пуша;
  - `autoBackupAfterFileChange` управляет режимом "после остановки правок".

## Наблюдение

При текущем конфиге плагин мог делать локальный commit по таймеру, но push на GitHub не планировался вообще, потому что интервал пуша был равен нулю.

## Вывод

Причина была в конфигурации, а не в GitHub и не в репозитории.

Исправление в актуальном `main`:

- `autoPushInterval` -> `1`
- `autoPullInterval` -> `5`
- `autoBackupAfterFileChange` -> `true`

## Следующий шаг

- Проверить в Obsidian, что после правки файла через несколько минут появляется новый commit и затем push в `main`.
- Если автосинхронизация всё ещё не срабатывает, проверить `Git is ready`, upstream branch и доступ к remote.
