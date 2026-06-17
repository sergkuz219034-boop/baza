# Hermes Telegram bridge deployment

Теги: #плейбук

## Назначение

Поднять Hermes runtime на сервере и понять, как подключить Telegram user-session для личного аккаунта Виктории.

## Что подтверждено кодом

- Hermes runtime в архиве разворачивается через `docker-compose.yml` с `nousresearch/hermes-agent:latest`.
- Telegram user bridge реализован в `tools/hermes_telegram_user_bridge.py`.
- Текущий bridge читает личную Telegram-сессию через `Telethon`, добавляет recruiting prompt, routing brief и подмешивает context из отдельного recruiter-vault перед ответом в private-чаты.
- Live vault для Виктории теперь отделён от общего export и лежит в `/home/codex/obsidian/hermes-victoria-vault`.
- Канон диалога: стадии `new / qualifying / qualified / offered` должен вести Hermes runtime; deterministic-слой bridge допустим только для operational-кейсов вроде `waiting_form`, `done`, `/clear`, late-contact и отправки анкеты после согласия.

## Runtime-факт

- На этом сервере прямой entrypoint `/usr/local/lib/hermes-agent/venv/bin/hermes` не годится: wrapper рекурсивный и ожидает `bash`.
- Рабочий путь для live bridge: импорт `run_agent.AIAgent` из `/usr/local/lib/hermes-agent`.
- В качестве transport endpoint Hermes runtime использует `http://127.0.0.1:3001/v1` и `FREELMAPI_API_KEY`.
- Значит ответ фактически идёт через Hermes runtime, а не через голый HTTP-вызов внутри bridge.

## Процедура

1. Развернуть Hermes runtime в отдельном каталоге вне wiki workspace и вне tracked repo.
2. Поднять контейнер из `docker-compose.yml`.
3. Проверить, что доступны:
   - `HERMES_HOME`
   - dashboard port `9119`
   - API port `8642`
4. Подготовить Telegram credentials:
   - `TG_API_ID`
   - `TG_API_HASH`
5. Первый запуск выполнить в интерактивном режиме и пройти:
   - ввод phone number;
   - code из Telegram;
   - 2FA password, если включён.
6. Проверить, что session file сохранился в `~/.hermes_user_bridge/telegram_user`.
7. Разместить отдельный recruiter-vault Виктории на сервере:
   - `00 Index.md`
   - `01 Routing Rules.md`
   - `02 Vacancies/*`
   - `03 Links.md`
   - `04 Objections.md`
   - `05 Style and Persona.md`
   - `06 Real Cases/*`
   - `07 T-Bank Cities.md`
8. В wrapper выставить:
   - `OBSIDIAN_VAULT_PATH=/home/codex/obsidian/hermes-victoria-vault`
   - `HERMES_BACKEND=runtime`
   - `HERMES_RUNTIME_PATH=/usr/local/lib/hermes-agent`
   - `HERMES_BASE_URL=http://127.0.0.1:3001/v1`
   - `HERMES_ENABLE_WEB_FALLBACK=1`
   - `REPLY_DELAY_SECONDS=14`
   - `REPLY_DELAY_JITTER_SECONDS=8`
   - `REPLY_MAX_WINDOW_SECONDS=22`
   - `FAST_FOLLOWUP_DELAY_SECONDS=5`
   - `FAST_FOLLOWUP_JITTER_SECONDS=5`
   - `QUALIFIED_REPLY_DELAY_SECONDS=8`
   - `QUALIFIED_REPLY_JITTER_SECONDS=6`
   - при необходимости можно переопределить:
     - `OFFER_FOLLOWUP_HOURS`
     - `OFFER_FINAL_PAUSE_HOURS`
     - `FORM_FOLLOWUP_HOURS`
     - `FORM_FINAL_PAUSE_HOURS`
   - если нужен remote gateway в desktop, указывать `https://ai.traffic-hubcrm.ru/v1`
9. Перезапустить bridge.
10. Отправить тестовое сообщение в private chat или вызвать `_ask_hermes(...)` одноразово и убедиться, что ответ идёт по новому routing.
11. После первого живого сообщения проверить, что появился файл `~/.hermes_user_bridge/chat_state.json`: в нём хранится stage диалога, ответы кандидата, последняя рекомендованная вакансия и факт отправки анкеты.
12. Перед server-side rollout прогнать локальную проверку:
   - `python tools/hermes_bridge_selftest.py`
   - она проверяет ключевые recruiter-сценарии на текущем bridge до выкладки на сервер:
     `Тетрика`, `Онекта`, `Т-Банк`, `Воксис`, post-form и objection-контур.
    - отдельное внимание держать на живых возражениях:
      `плохие отзывы`, `развод`, `это продажи?`, `это холодные звонки?`
    - отдельно проверить, что deterministic-layer не перехватывает обычную квалификацию:
      `привет`, многострочный ответ на 5 пунктов, `расскажите подробнее`, короткое `Был / Да / 8 часов / Москва`
13. Если включён follow-up контур, убедиться, что он работает мягко:
   - не чаще одного касания на этап;
   - не отправляет follow-up, если кандидат уже ответил после оффера или после ссылки.

## Что проверять после запуска

- Hermes gateway живой и не падает после рестарта.
- Telegram session не теряется между перезапусками.
- Bridge не отвечает в группах и не обрабатывает не-private сообщения.
- `last_seen.txt` обновляется, чтобы не было повторных ответов на старые сообщения.
- У нового vault не смешиваются старые generic-заметки и recruiter brain Виктории.
- Если ответы внезапно перестали приходить, первым делом проверить `run_agent` import, `FREELMAPI_API_KEY`, `HERMES_BASE_URL` и доступность `OBSIDIAN_VAULT_PATH`.
- Если нужен публичный desktop remote gateway, проверить `ai.traffic-hubcrm.ru`: домен должен reverse_proxy'иться на Hermes backend, а не редиректить на внешний сайт.
- Если включён web fallback, factual-детали о компании и вакансии брать только с официальных или первичных источников; не полагаться на отзывы и неофициальные пересказы.
- Если bridge стартует, но сразу падает, проверить `argv`-очистку, line endings у wrapper и права на `~/.hermes_user_bridge`.

## Если нужен серверный вариант

Если bridge должен жить именно на сервере, а не на рабочей машине, это уже отдельная задача на адаптацию:

- определить systemd/compose wrapper;
- решить, где хранится session file;
- проверить, как обрабатываются 2FA и повторная авторизация после перезапуска.
- проверить, где лежит Obsidian vault и не надо ли ограничить retrieval по подкаталогам.
- если bridge запускается от `codex`, проверить права на `~/.hermes_user_bridge` и перенос session sqlite без root ownership.
- не рассчитывать на прямой `hermes` entrypoint, пока не исправлен его wrapper.

## Смежные страницы

- [[2026-06-12 hermes deploy and telegram user bridge]]
- [[Integrations]]
- [[Deployment]]
