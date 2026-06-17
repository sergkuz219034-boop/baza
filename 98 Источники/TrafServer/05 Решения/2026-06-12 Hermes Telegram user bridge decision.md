# Hermes Telegram user bridge decision

Теги: #решение #интеграции

## Проблема

Нужно понять, как Hermes должен работать с Telegram-аккаунтом Виктории после переноса на сервер.

## Контекст

- В архиве Hermes есть container-based runtime (`docker-compose.yml`).
- В проекте есть отдельный `tools/hermes_telegram_user_bridge.py`.
- Bridge использует `Telethon` и личную Telegram session, а не bot token.

## Решение

Использовать схему user-session bridge:

- Hermes runtime разворачивать отдельно;
- Telegram-авторизацию делать через личную сессию Виктории;
- session file хранить отдельно и не считать его переносимым без проверки;
- bridge запускать только там, где доступен рабочий runtime и рабочий LLM backend;
- recruiter/persona prompt, routing brief и Obsidian retrieval держать в самом bridge, а не в Telegram-чате вручную;
- В live deployment bridge можно запускать от `codex`, если сессия Telethon и Obsidian vault лежат в writable каталогах этого пользователя.
- Для Виктории использовать отдельный recruiter-vault, а не весь старый export переписок.
- Ответ генерировать через Hermes core `run_agent.AIAgent`; Python в bridge использовать только как transport/runtime glue.
- Считать анти-паттерном ситуацию, когда Python-мост сам генерирует recruiter-диалог на стадиях `new / qualifying / qualified / offered`.
- Ввести искусственную задержку ответа около минуты после последнего входящего сообщения кандидата.
- Публичную точку входа Hermes публиковать через `ai.traffic-hubcrm.ru`, а не через редирект на внешний сайт.
- Для remote gateway использовать `https://ai.traffic-hubcrm.ru/v1` как базовый URL, потому что backend на сервере слушает путь `/v1` и отвечает на API-запросы там.

## Последствия

- Личный Telegram-аккаунт можно использовать как раньше, если пройти интерактивную авторизацию и сохранить session.
- Перенос на сервер не является "drop-in" операцией: местоположение bridge и способ вызова `hermes` нужно определить заранее.
- Bot token не нужен для этой схемы, но это увеличивает чувствительность к хранению session и 2FA.
- Если прямой `hermes` entrypoint нерабочий, не надо путать это с отказом Hermes в целом: рабочий слой здесь — `run_agent` из того же runtime.
- OpenAI-compatible endpoint (`FreeLLMAPI`) остаётся transport dependency Hermes runtime, но не заменяет сам recruiting brain.
- Obsidian/context retrieval добавляет файловый I/O на каждый запрос, поэтому нужен лимит по размеру выборки и понятный default vault path.
- Shell wrapper должен быть LF-only; иначе bash на сервере подсовывает `\r` в путь к python-скрипту.
- Delay-режим делает ответы человечнее, но повышает риск накопления нескольких сообщений до ответа; bridge поэтому должен дебаунсить и отвечать после последнего сообщения, а не после первого.
- Если bridge снова разрастается deterministic-ветками поверх основной квалификации, Hermes перестаёт быть dialogue brain и начинает повторять уже отвеченные вопросы; это считать регрессией.
- Если `ai.traffic-hubcrm.ru` случайно снова становится редиректом, remote gateway ломается: это надо считать инфраструктурной регрессией.

## Альтернативы

- Telegram bot token flow. Проще для server-only daemon, но это уже не личный аккаунт Виктории.
- Оставить bridge на рабочей машине и вызывать удалённый Hermes runtime. Менее удобно для серверного ops, но снижает требования к серверной обвязке.
- Оставить общий Obsidian export как единый источник для рекрутера. Отклонено: retrieval тонет в шуме и вытаскивает неактуальные формулировки.
