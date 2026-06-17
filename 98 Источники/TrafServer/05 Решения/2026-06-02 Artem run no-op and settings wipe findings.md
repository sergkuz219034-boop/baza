# Artem: run no-op and settings wipe findings

Дата: 2026-06-02

Связанные документы:
- [2026-06-02 Artem full cycle upload and send root cause.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-02%20Artem%20full%20cycle%20upload%20and%20send%20root%20cause.md)
- [2026-06-01 consolidated runtime patch bundle.md](C:/Users/Арт/Desktop/TrafServer/05%20Решения/2026-06-01%20consolidated%20runtime%20patch%20bundle.md)

## Анализ

На `2026-06-02` у `Artem` проявились два новых симптома из UI:

1. после нажатия `Полный цикл` в логе виден только маркер запуска;
2. после сохранений из интерфейса почти стираются настройки.

По текущему коду подтверждено следующее.

### Симптом 1. `Полный цикл` может выглядеть как “ничего не происходит”

В job-runner:

- [jobs.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/routers/jobs.py)
  - статус `running` выставлялся ещё до фактического захвата `_cycle_running`;
  - если lock уже занят другим контуром, worker тихо возвращался в `idle`.

Это создавало плохой UX-сценарий:
- UI уже считает, что job стартовал;
- реальный full cycle мог не начаться;
- явного сигнала `cycle_busy` не было.

Для этого симптома наиболее вероятные причины были:

1. `High`, вероятность `0.60`
- hidden busy-cycle path:
  - `_cycle_running` уже занят другим потоком/контуром.

2. `Medium`, вероятность `0.25`
- ранняя ошибка до первой фазы внутри worker path, но без достаточной прозрачности для UI.

3. `Low/Medium`, вероятность `0.15`
- визуальная задержка/отсутствие явного push-обновления в UI при раннем завершении worker.

### Симптом 2. Настройки могли затираться через `null` в PATCH payload

В settings router:

- [settings.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/routers/settings.py:549)
- [settings.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/routers/settings.py:561)
- [settings.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/routers/settings.py:588)

PATCH-роуты делали:
- `patch.model_dump(exclude_unset=True)`
- затем напрямую `_apply_editable_patch(config, data)`

Если фронт присылал поле как явно заданное `null`, backend трактовал это как намеренное новое значение и затирал существующую настройку.

Это хорошо объясняет пользовательский симптом:
- “почти все настройки стираются”

Наиболее вероятная причина здесь:

1. `High`, вероятность `0.80`
- UI отправляет partial payload с частью полей в `null`;
- backend без фильтрации сохраняет эти `null` поверх рабочего конфига.

## Причина

### 1. `High`: PATCH settings path не был защищён от `null`-затирки

- Описание проблемы:
  - частичный PATCH мог обнулить существующие значения.
- Первопричина:
  - backend не отбрасывал `None`-значения перед `_apply_editable_patch(...)`.
- Возможные последствия:
  - потеря spreadsheet IDs;
  - потеря периодов/флагов;
  - деградация `vbiv`/`superjob` настроек.

### 2. `Medium/High`: run-button path не сигнализировал “busy cycle” заранее

- Описание проблемы:
  - пользователь видел запуск, но фактический worker мог сразу выйти.
- Первопричина:
  - preflight-проверка общего `_cycle_running` отсутствовала;
  - ранний skip не транслировался в UI как отдельная причина.
- Возможные последствия:
  - ложное ощущение, что “полный цикл завис”;
  - трудная диагностика busy-state.

## План исправления

На этом шаге внесены два hardening-исправления:

1. settings PATCH:
- игнорировать `None`-значения в patch payload.

2. jobs run:
- проверять `_cycle_running.locked()` до старта worker;
- при раннем skip транслировать `job_skip` с `reason=cycle_busy`.

## Diff

Изменены файлы:

- [remote_server_snapshot/api/routers/settings.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/routers/settings.py)
- [remote_server_snapshot/api/routers/jobs.py](C:/Users/Арт/Desktop/TrafServer/remote_server_snapshot/api/routers/jobs.py)
- [remote_files/api/routers/settings.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/settings.py)
- [remote_files/api/routers/jobs.py](C:/Users/Арт/Desktop/TrafServer/remote_files/api/routers/jobs.py)

Суть изменений:

```diff
def _drop_none_values(data: dict) -> dict:
    return {key: value for key, value in data.items() if value is not None}
```

```diff
- data = patch.model_dump(exclude_unset=True)
+ data = _drop_none_values(patch.model_dump(exclude_unset=True))
```

```diff
if leads_service._cycle_running.locked():
    raise HTTPException(status_code=409, detail="Полный цикл уже выполняется в другом процессе или потоке")
```

```diff
_broadcast_ws({
    "type": "job_skip",
    "command": command,
    "status": "idle",
    "reason": "cycle_busy",
})
```

## Риски

### Низкие

- если какой-то клиент специально хотел очищать поле через `null`, теперь это поведение больше не сработает.

Почему это приемлемо:
- для осознанной очистки безопаснее использовать пустую строку, `false`, `0` или пустой список по типу поля;
- `null` для runtime-настроек оказался слишком опасным.

### Оставшиеся

- это не доказывает, что hidden busy-cycle path уже точно был активной причиной у `Artem`;
- но теперь система хотя бы перестаёт скрывать этот сценарий.

## Проверка после исправления

Подтверждено:

1. Изменённые файлы компилируются без синтаксических ошибок.
2. PATCH settings path больше не передаёт `None` дальше в `_apply_editable_patch`.
3. run path теперь заранее отклоняет старт, если `_cycle_running` уже занят.
4. ранний skip теперь имеет явный reason `cycle_busy`.

## Дополнительные улучшения

Следующий полезный шаг:

1. проверить реальный payload, который фронт отправляет в `/api/settings` для `Artem`;
2. отдельно проверить, воспроизводится ли `409 cycle busy` после нажатия `Полный цикл`;
3. затем уже продолжить runtime-ветку:
- честный `run_status`
- retry lifecycle
- retry payload enrichment
