# 2026-06-25 Standalone content bot generation bypassed preview

## Симптом

- после генерации вакансии бот публиковал её сам без этапа предпросмотра;
- пользователь не видел черновик, не мог отредактировать текст и не подтверждал публикацию.

## Зона системы

- live repo: `/root/TrafficHub`
- bot source: `/root/TrafficHub/standalone_content_bot/app.py`
- функция: `finish_flow`

## Гипотеза

- флаг автопостинга использовался не только для scheduler-публикаций по расписанию, но и для немедленной публикации любого только что сгенерированного черновика.

## Проверка

- в `finish_flow` после `save_draft(...)` и `store_generation(..., "draft")` был блок:
  - `if await autopost_enabled():`
  - `publish_draft(bot, message.from_user.id)`
- этот код срабатывал сразу после генерации поста/вакансии и обходил UX-этап:
  - предпросмотр;
  - ручное редактирование;
  - явное подтверждение публикации.
- scheduler по времени находится отдельно в `autopost_scheduler` и публикует через `publish_autopost_to_channel`.

## Наблюдение

- под одним toggle `autopost_enabled` были смешаны два разных контура:
  - scheduled channel autopost;
  - immediate publish after generation.
- из-за этого включение автопостинга ломало базовую логику черновика.

## Вывод

- генерация контента должна всегда заканчиваться сохранением черновика и показом предпросмотра;
- scheduled autopost должен работать только через `autopost_scheduler`, а не через пользовательский flow создания поста/вакансии.

## Следующий шаг

- если потребуется отдельный режим "публиковать сразу после генерации", его надо выносить в отдельную явную настройку, а не совмещать с расписанием.

## Дополнение: внешний toggle из Account Manager

### Симптом

- standalone content bot был отдельным контейнером `traffichub_standalone_content_bot`;
- в Account Manager не было явной вкладки, которая включает или выключает именно этот bot-контур.

### Зона системы

- UI: `/root/TrafficHub/AccountManager/dashboard/index.html`, `app.js`, `css/app.css`
- API: `/root/TrafficHub/AccountManager/api/routers/content.py`
- service: `/root/TrafficHub/AccountManager/services/content_bot_service.py`
- bot: `/root/TrafficHub/standalone_content_bot/app.py`
- runtime state: `AccountManager/data/runtime/content_bot_state.json`
- docker compose: общий mount `./AccountManager/data/runtime:/shared_runtime` для standalone bot

### Проверка

- `GET /api/content/settings` возвращает `bot_enabled`;
- `PUT /api/content/settings` с `bot_enabled` пишет:
  - `AppSetting.content_bot_enabled`;
  - общий JSON-файл `content_bot_state.json`;
- standalone bot читает тот же файл через `CONTENT_BOT_STATE_FILE`;
- при `enabled=false` bot продолжает polling, но пользовательские сценарии и scheduler-autopost блокируются.

### Вывод

- переключатель теперь управляет не только UI, а реальным runtime-флагом;
- источник runtime-состояния для этого toggle — общий файл, доступный Account Manager и standalone bot;
- отсутствие state-файла трактуется как `enabled=false`, чтобы не было скрытого включения после деплоя.
