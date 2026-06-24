# Graphify architecture scan

## Назначение
Graphify используется как быстрая навигационная карта по актуальному server snapshot или `remote_files`. Он не является источником истины: любые выводы подтверждаются кодом, runtime, БД или контейнерами.

## Когда запускать
- перед крупным расследованием архитектуры;
- когда нужно быстро найти связи роутера, сервиса и runtime-хранилища;
- когда новый агент должен понять карту проекта без полного чтения всех файлов.

## Команды
Локально, из `C:\Users\Арт\Desktop\TrafServer`:

```powershell
graphify update .\remote_files --no-cluster
graphify explain jobs.py --graph .\remote_files\graphify-out\graph.json
graphify explain leads_service.py --graph .\remote_files\graphify-out\graph.json
```

## Правила
- Не коммитить generated graph как архитектурную правду.
- Не использовать старую wiki вместо проверки по коду.
- Если Graphify показывает связь, открыть соответствующий файл и подтвердить поведение.

## Связанные заметки
- [[Runtime doctor]]
- [[Runtime Inspector]]
- [[Job Queue]]

