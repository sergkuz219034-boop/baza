# 2026-06-29 admin password update failed

Теги: #debug

## Симптом

В admin panel TrafficHub при смене пароля у license account показывался общий toast `Не удалось обновить`. По скриншоту проблема проявлялась на строке пользователя `Artem`: поле пароля принимало ввод, но сохранение не проходило.

## Зона проекта

- Live server repo: `/root/TrafficHub`
- Frontend: `dashboard/app.js`
- API: `api/routers/settings_license_accounts.py`
- License layer: `utils/license.py`
- Runtime DB: PostgreSQL таблицы license/auth пользователей
- GitHub commit: `5052df50b` (`Fix admin license password updates`)
- Связанные заметки: [[License layer]], [[Runtime database]]

## Текущая гипотеза

Backend отклоняет короткий рабочий пароль, а frontend скрывает реальную причину ошибки.

## Проверки

### Проверка 1

- Что сделал: проверил live-код `/root/TrafficHub/utils/license.py`.
- Что ожидал: найти validation rule для нового пароля.
- Что увидел: `_validate_new_password()` требовал минимум 10 символов, при этом в текущем рабочем контуре используются короткие operator-пароли вроде `1881`.

### Проверка 2

- Что сделал: проверил `dashboard/app.js` вокруг admin license accounts.
- Что ожидал: увидеть вывод backend error detail.
- Что увидел: `saveLicenseField()` показывал только общий текст `Не удалось обновить`, не возвращал статус успеха/ошибки, а поле пароля могло очищаться после отказа backend.

### Проверка 3

- Что сделал: на live-сервере изменил правило в `utils/license.py`, frontend-поведение в `dashboard/app.js`, добавил regression test.
- Что ожидал: пароль `1881` проходит validation, placeholder/mask всё ещё запрещены.
- Что увидел: `python -m pytest tests/test_license_password_validation.py -q` вернул `7 passed`.

### Проверка 4

- Что сделал: создал временного пользователя в PostgreSQL через live-контейнер, сменил ему пароль на `1881`, проверил old/new login.
- Что ожидал: старый пароль не работает, новый работает.
- Что увидел: `validate_old False`, `validate_new True`.

### Проверка 5

- Что сделал: пересобрал и перезапустил live service `autolead_bot`, проверил public asset.
- Что ожидал: публичный `/app.js` содержит новый текст кнопки и подробную ошибку.
- Что увидел: `https://traffic-hub.pro/app.js` отдаёт обновлённый JS; `https://traffic-hub.pro/api/health` отвечает `status=ok`.

## Наблюдения

- `traffic-hubcrm.ru` сейчас отдаёт страницу переезда на `traffic-hub.pro`; live-проверки этой правки выполнялись через `traffic-hub.pro`.
- На сервере до правки уже были unrelated dirty files по `AccountManager`, `standalone_content_bot`, `README.md`, `docker-compose.yml`; их нельзя считать частью этого исправления.
- Кнопка `Сброс` в admin license accounts фактически сохраняла введённый пароль, поэтому label вводил в заблуждение.

## Вывод

Подтверждён root cause: backend-валидация была строже реального рабочего процесса, а frontend скрывал точную ошибку. Правка на live-сервере:

- минимальная длина нового пароля снижена с 10 до 4 символов;
- служебные значения `пароль установлен`, `не задан`, `********` по-прежнему запрещены;
- frontend показывает backend error detail;
- поле пароля не очищается, если backend отказал;
- кнопка переименована в `Сохранить`.

## Следующий шаг

Если после hard refresh пароль всё ещё не сохраняется, проверять уже не validation, а конкретный ответ `PATCH /api/settings/license-accounts/{login}` и наличие пользователя в PostgreSQL license store.

## Связанные заметки

- [[License layer]]
- [[Runtime database]]
