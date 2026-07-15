# Changelog

- В dashboard Telegram HR Agent добавлена bot-specific температура: ползунок `0,0–2,0`, API-валидация, хранение в `extra_config.temperature` и применение в LLM payload. Live значение `HR Виктория` инициализировано как `0,4`; product commit `51ed7d2c4`.
- Исправлены повторяющиеся fallback-ответы Telegram HR Agent: устойчивый разбор JSON/fenced JSON/plain text, контекст предыдущих реплик, приоритет прямого ответа над повторным приветствием. Live prompt скорректирован, модель переключена с нестабильной `openrouter/free` на `openai/gpt-4.1-mini`; commits `eb39bdc1a`, `c3b6999d5`.
- Telegram HR Agent теперь отмечает входящие Business-сообщения прочитанными через `readBusinessMessage` перед статусом `typing`; вызов использует исходные `business_connection_id`, `chat_id`, `message_id` и не блокирует ответ при ошибке. Live smoke успешен; product commit `16fe24448`.
- В Telegram HR Agent добавлен естественный темп ответа: `typing` до и во время генерации с обновлением каждые 4 секунды, сохранение `business_connection_id`, задержка 0,8–4,0 секунды и non-blocking обработка ошибок chat action. Live Business smoke успешен; product commit `3765f4178`.
- В Telegram HR Agent добавлен редактируемый системный промт каждого bot binding: UI/API/runtime, лимит 12 000 символов, защита `business_connections`, regression на изоляцию промтов. Live HR LLM включён через OpenRouter env secret; product commit `b369dea66`.
- Исправлена наблюдаемость Telegram HR Agent: commit `39ec17913` сохраняет события `business_connection` в owner-scoped binding. Подтверждено, что `@Vectoria101_bot` и webhook исправны, но реальные Telegram Business-аккаунты ещё не подключены; legacy `hr_ai_worker` не считается multi-account runtime.

# 2026-07-09

- В `AccountManager` исправлен системный Telethon-bug для legacy Telegram `tdata`: `services/content_parser.py` больше не создаёт новый UUID `.session` на каждый check/read, а использует стабильный `legacy_account_{id}.session` с per-account lock и cleanup старых session-артефактов.
- Для `AuthKeyDuplicatedError` добавлено явное сообщение восстановления: текущий `tdata/session` уже инвалидирован Telegram и требует reimport новой авторизованной `tdata`.
- Добавлены regression-тесты `tests/test_account_manager_telethon_session_files.py` на стабильный session path, cleanup старых UUID-session и user-facing duplicated-key message.

# 2026-07-01

- Подтверждён root cause массовых строк Зарплата.ру в Google Sheets за `01.07.2026`: `normalize_resume()` ставил текущую дату выгрузки, а `import_resumes()` пропускал search-result записи без телефона/email. На сервере исправлено в commit `ba15d7a59`, CHANGELOG-кодировка поправлена в `dbe7a30a6`; добавлено расследование и обновлена сущность [[Zarplata.ru integration]].

# 2026-06-30

- Для профиля `artem` на live-сервере подтверждён owner-scoped Rabota.ru proxy: `proxy_enabled=true`, `proxy_url=http://uE0D08:LZCcvM@217.29.62.68:8000`; другие пользователи не изменялись.
- Content Bot: перед публикацией поста удаляются ссылочные плейсхолдеры из текста (`[вставьте ссылку]`, `[ваша ссылка]`, `ваша_ссылка_здесь`, `example.com`), а ссылка остаётся только в inline-кнопке `Перейти на сайт -> https://hrcadry.pro`. Серверный commit: `4d07384c4`.
- Исправлена неполная выгрузка Зарплата.ру: импорт теперь объединяет `/resumes`, `/resumes?only_in_responses=true` и резюме из коллекций `/negotiations` по активным вакансиям работодателя; collection-запросы не ограничиваются `status=active`.
- Добавлены промежуточные stdout-события прогресса Зарплата.ру, чтобы dashboard не выглядел зависшим во время долгого обхода API.
- Добавлены regression-тесты `tests/test_zarplata_api.py` на `only_in_responses`, отсутствие `status` в `/negotiations` и импорт резюме из collection items.
- Исправлена вечная строка `Полный цикл выполняется` после очистки логов/пустой очереди: dashboard теперь сразу удаляет realtime spinner при `status=idle` без `job_id`. Серверный commit: `1b3030124`.
- Исправлена “тишина” на фазе `Сбор лидов с Rabota.ru`: добавлены видимые business-progress строки по началу загрузки откликов и постраничному прогрессу. Серверный commit: `c52019bd4`.
- Исправлена новая анкета Самокат в фактическом runtime path `SamokatLeadsuPlatform`: скрытая `button.btn_form` больше не считается отсутствующей кнопкой, форма отправляется через JS `requestSubmit/submit`. Серверный commit: `0b2518036`.
- Исправлена ошибка Зарплата.ру `you can't look up more than 2000 items`: `/resumes` больше не запрашивает страницы глубже API depth limit, полный цикл продолжает работу и добирает отклики через `/negotiations`. Серверный commit: `860adb539`.
- Исправлен повтор Самокат-ошибки из-за drift между `traffichub_app` и `traffichub_worker`: form-fill hotfix синхронизирован в оба контейнера, LFID/blank/chrome-error без формы теперь transient, а не permanent submit failure. Серверный commit: `3b3317f7d`.
- Устранён повтор из-за неполной доставки hotfix в worker: `zarplata_api.py` и Samokat missing-form fallback синхронизированы в `traffichub_app` и `traffichub_worker`, оба контейнера прошли одинаковый набор targeted tests. Серверный commit: `59f7a906a`.
- Сокращён UI-лог Зарплата.ру до короткого итога; transient landing-ошибки офферов теперь идут как warning/retry, а не красный permanent error. Серверный commit: `94e2f428f`.

# 2026-06-29

- Добавлены загрузка и выгрузка лидов в Excel/CSV: `GET /api/leads/export.xlsx`, `POST /api/leads/import`, UI-кнопки в базе лидов, regression-тесты. Серверный commit: `a04351895`.
- Разобрана причина старой Google Sheets таблицы `10tCmh8Z...`: ID хранился в legacy-поле `admin.google_sheets.spreadsheet_id`; поле очищено на live, рабочие `pending/processed` ID не менялись.
- Исправлен порядок полного цикла: Rabota.ru сначала собирает и выгружает лиды в Google Sheets, затем запускается Зарплата.ру, после чего общий sender обрабатывает единую pending-очередь обоих источников. Серверный commit: `d2c4c0256`.
- Усилен owner-guard Зарплата.ру: выгрузка запускается только когда у текущего пользователя включён `enabled`, заполнены `client_id/client_secret` и есть user OAuth `access_token`. App-token-only или частично настроенные профили не запускают импорт и не выгружают резюме.
- Исправлен формат ссылок Rabota.ru в Google Sheets: для откликов поле `Резюме` теперь выгружается как `/resume-search/{resume_id}/?source=response&vacancy_id={vacancy_id}&response_id={response_id}`. Старый `/resume/{resume_id}` оставлен только как fallback при отсутствии контекста отклика.
- Исправлен live-баг Зарплата.ру: старый config мог хранить `enabled=true` вместе с `enable_form_fill=false`, из-за чего новые лиды выгружались в Google Sheets со статусом `заполнение выключено` и не попадали в заполнение анкет. Backend теперь нормализует один UI-переключатель как `сбор + заполнение`, live config `admin` мигрирован, добавлены regression-тесты.
- Зафиксировано расследование по сбою смены пароля license account в TrafficHub admin panel: root cause был в слишком строгой backend-валидации коротких рабочих паролей и скрытой ошибке на frontend.
- Обновлена сущность [[License layer]]: правило пароля теперь описано как минимум 4 символа с запретом служебных placeholders/masks.
- Исправлено live-удаление обзорных Telegram-аккаунтов в `AccountManager`: экран `Подключенные аккаунты` удаляет generic `accounts` через `/api/accounts/{id}`, поэтому backend теперь сначала отвязывает связанные `RequestLog` / `ContentSource` / `PostingTarget` / `PostingTask` / `ContentLog`, а для `platform="tg"` дополнительно останавливает живой профиль перед delete.
- Исправлен frontend live `AccountManager/dashboard/app.js`: кнопка удаления аккаунта теперь показывает success/error toast вместо молчаливого провала.
- На live-сервере пересобран и перезапущен контейнер `traffichub_account_manager`; health после рестарта зелёный.
- Исправлено удаление Google-аккаунта в `AccountManager`: перед `DELETE /api/google/accounts/{id}` backend теперь удаляет зависимые `social_accounts`, чтобы операция не падала на FK и не выглядела как "аккаунт не удаляется".
- Добавлены wiki-заметка расследования и сущностная заметка по зависимостям `google_accounts -> social_accounts`.

# 2026-06-17

- Доведён server-side Hermes Workspace: `pnpm install` завершён на live-сервере, Vite UI поднят на `:3000`, локальный health-check `http://127.0.0.1:3000/hermes/` отвечает `200`.
- Публичная точка входа для кнопки из AccountManager перенесена на `https://am.traffic-hubcrm.ru/hermes/`, чтобы не упираться в отдельный basic-auth perimeter `ai.traffic-hubcrm.ru`.
- Обновлены snapshot, deployment docs и wiki: старое описание redirect через `ai.traffic-hubcrm.ru/hermes` помечено устаревшим.
- Исправлен фактический переход из вкладки Hermes: sidebar-tab `ИИ Агент -> Hermes` теперь сразу открывает `/hermes/`, а Caddy проксирует Workspace через рабочий gateway `172.22.0.1:3000`.
- Добавлен `victoria-recruiter-gateway.service` на live-сервере: OpenAI-compatible API на `127.0.0.1:8642` привязывает Hermes Workspace к recruiter brain Виктории и vault `/home/codex/obsidian/hermes-victoria-vault`.
- Добавлен локальный исходник gateway: `tools/recruiter_workspace_gateway.py`.

# 2026-06-16

- В AccountManager карточка `Hermes` теперь показывает `outsourc-e/hermes-workspace` вместо старого `fathah/hermes-desktop`.
- Подтверждено, что внешний путь через `ai.traffic-hubcrm.ru/hermes` не закрывает user-flow из AccountManager из-за отдельной basic-auth ступени; решение перенесено в запись от `2026-06-17`.

# 2026-06-12

- Зафиксирован Hermes runtime perimeter: архив `hermes_project.zip`, Telegram user-session bridge и ограничения server deployment отражены в wiki.
- Добавлены расследование `01 Расследования/2026-06-12 hermes deploy and telegram user bridge.md`, playbook `03 Плейбуки/Hermes Telegram bridge deployment.md` и решение `05 Решения/2026-06-12 Hermes Telegram user bridge decision.md`.
- Обновлены `02 Архитектура/Integrations.md` и `02 Архитектура/Deployment.md` под подтверждённую схему Hermes.
- Hermes user-session bridge развернут на сервере `150.241.70.31`, авторизация через номер и код завершена, session сохранена в `/root/.hermes_user_bridge/telegram_user`.
- Исправлен Telegram bridge runtime: ответы теперь идут через локальный `FreeLLMAPI` fallback, потому что прямой `hermes chat` на сервере не возвращал текст в разумный срок.
- В `tools/hermes_telegram_user_bridge.py` восстановлен recruiter/persona prompt и добавлен Obsidian/wiki retrieval по markdown-заметкам перед запросом к LLM backend.
- Документация синхронизирована под новый bridge-контур; серверный процесс нужно перезапустить после копирования обновлённого скрипта.
- Серверный bridge доведён до рабочего состояния под `codex`: session перенесена в `/home/codex/.hermes_user_bridge`, vault загружен в `/home/codex/obsidian/wiki/traffichubserver/wiki/TrafficHub-obsidian`, bridge стартует без root ownership ошибок и печатает `Bridge connected as Виктория id=8127966108`.
- Исправлены два runtime-краевых случая: `readonly database` у Telethon session и LF/CRLF-артефакт в shell wrapper.
- Собран отдельный recruiter-vault `docs/hermes-victoria-vault` для Виктории: routing rules, style/persona, вакансии, objections, актуальные links, real cases и нормализованная матрица `Т-Банка` по регионам.
- `tools/hermes_telegram_user_bridge.py` переделан в recruiting-brain: добавлены signal extraction, routing brief, приоритетный retrieval и fallback-safe матчинги по `Т-Банку`.
- Live-сервер переведён с общего Obsidian export на `/home/codex/obsidian/hermes-victoria-vault`.
- Генерация ответа переведена на Hermes core `run_agent.AIAgent`; HTTP-вызов оставлен только как запасной fallback, а не основной backend.
- В bridge добавлен debounce-режим с задержкой примерно в минуту после последнего сообщения кандидата, чтобы ответы выглядели ближе к живому HR.
- Первый контакт дополнительно ужесточен: при пустом или старом запросе bridge теперь сначала проводит квалификацию, а не предлагает случайную вакансию.
- Для `Тетрики` зафиксирована отдельная инструкция при отправке анкеты: указать цифру `3` в строке опыта и вставить актуальную ссылку на резюме, если анкета её просит.
- Добавлена початовая память в bridge: теперь состояние кандидата сохраняется в `chat_state.json` и переживает новые сообщения и перезапуск процесса.
- По реальным чатам `ChatTG` ужесточён deterministic routing: `расскажите подробнее` больше не считается согласием на анкету, добавлены сигналы `нет тишины`, `старая чат-вакансия` и `уже пробовал Воксис`.
- Уточняющие сообщения bridge стали короче: если не хватает только одного поля, Hermes спрашивает только его, а не повторяет весь опрос.
- Vault Виктории дополнен кейсом `old_chat_vacancy_noexp_city_first.md` и обновлёнными правилами по сценариям `только чаты` и `без звонков`.
- Добавлен capped debounce для Telegram bridge: базовая задержка снижена до `45-70` секунд, а серия коротких сообщений теперь ограничена общим потолком `90` секунд.
- Vault Виктории дополнен кейсами `experienced_only_chats_route_to_onekta.md` и `name_actual_vacancy_after_old_project.md`.
- При server-side перезапуске повторно подтверждён CRLF-риск в `run_hermes_user_bridge.sh`; wrapper нормализован в LF перед live-стартом.
- Добавлена автоматическая цепочка переходов после отказа от оффера: `Тетрика -> Онекта -> Т-Банк -> Воксис`, без повторного общего опроса.
- Vault Виктории дополнен кейсом `rejection_chain_offer_to_next.md`.
- Уточнён канон вакансий по замечанию пользователя: `Онекта` закреплена как звонковый формат, `Т-Банк` как `чаты + звонки`, чисто чатовые вакансии убраны из описаний и routing-формулировок.
- Закрыт новый класс recruiter-routing сбоев на живых коротких репликах кандидата: добавлены phrase-match helper'ы для `а какие еще есть вакансии?` и `есть что-то с чатами?`, отдельная deterministic-ветка `Т-Банка` на ответ только городом (`Москва`, `Челябинск` и т.д.) и защита от ложного извлечения города из сервисных фраз вроде `расскажите подробнее`.
- Добавлен objection-layer для доверия к вакансии и процессу: отработки на `обман/лохотрон/плохие отзывы`, страх анкеты и ссылок, вопросы по данным, ограничения по не-РФ оформлению и возражение `маленькая зарплата`.
- Vault Виктории дополнен кейсами `scam_reviews_link_fear.md` и `form_data_nonrf_salary_objections.md`.
- Добавлены conversion-отработки перед анкетой: `я подумаю`, `не сейчас`, вопросы про `цифру 3`, ссылку на резюме и прошлый неудачный опыт в похожей работе.
- Vault Виктории дополнен кейсом `thinking_resume_experience3_objections.md`.
- Доработан следующий слой возражений по реальным чатам: `самозанятость / ТК РФ`, `я откликался на чаты, а тут звонки`, `заполнил анкету, но не связались`, `дома нет тишины`.
- Vault Виктории дополнен кейсами `old_chat_vacancy_mismatch.md` и `no_callback_after_form.md`.
- Ускорен live-ритм ответа: базовая серверная задержка сокращена до диапазона около `25-37` секунд, общее окно пачки сообщений ограничено `45` секундами, а короткие догоняющие сообщения после оффера обрабатываются отдельным быстрым режимом.
- Добавлена отдельная отработка на кейс `в вакансии написано одно, а по факту другое`; vault дополнен кейсом `misleading_old_ad_salary_and_calls.md`.
- Добавлен локальный сценарный self-test `tools/hermes_bridge_selftest.py`: он проверяет routing, разбор структурированных ответов, стартовые фразы, post-form ветки и правило `не отправлять анкету по случайному "да"`.
- Улучшен разбор ответов кандидата в Telegram-формате: теперь bridge лучше понимает ответы по пунктам, построчные ответы и короткие фрагменты через запятую.
- Self-test расширен до матрицы ключевых recruiter-кейсов: `Тетрика`, `Онекта`, `Т-Банк` по Самаре, fallback по неизвестному городу, `Воксис`, `ты бот?`, цепочка отказов и post-form сценарии.
- В bridge добавлен мягкий follow-up контур: отдельный пинг после оффера, отдельный пинг после отправки анкеты и финальное `ставлю диалог на паузу`, если кандидат пропал.
- Расширен deterministic objection-layer для живых сомнений кандидата: `негативные отзывы`, `пишут что развод`, `это продажи?`, `это холодные звонки?`, с честными vacancy-specific ответами по `Тетрике`, `Онекте`, `Т-Банку` и `Воксису`.
- По новому циклу анализа `ChatTG` bridge ускорен на понятных сообщениях кандидата: полный ответ на опрос, короткие objections и стадия `qualified` теперь идут через отдельный быстрый delay-профиль; server wrapper переведён на более короткое окно ответа `14-22` секунд с ещё более быстрым follow-up и offer-режимом.
- Дополнительно добавлены deterministic-ветки на кейсы `почему написали только сейчас / почему вакансия ещё активна` и `ограничение по речи / нужны только чаты`, чтобы Hermes не тащил в неподходящий голосовой оффер.
- Исправлен разбор коротких кандидатских ответов: `не было` теперь считается ответом `нет опыта`, а generic-сообщения вроде `привет` больше не затирают поле города. За счёт этого сценарий `оператор чата -> не было -> Москва` корректно маршрутизируется в `Т-Банк`.
- В Telegram user-session bridge добавлена имитация `typing` перед отправкой ответа, чтобы в диалоге от аккаунта Виктории показывался статус `печатает`.
- Убран повтор одного и того же waiting-form ответа: для `есть другие вакансии`, `ещё не вышли` и повторных generic ping добавлены отдельные deterministic-ветки, чтобы bridge не зацикливался на одном и том же вопросе про заполнение анкеты.
- Recruiter-vault обновлён по новым файлам пользователя: расширена карточка `Тетрики`, детализирована `Онекта`, обновлён `Т-Банк` под новую xlsx-матрицу и добавлен отдельный geo-note по `Voxys`.
- В runtime-контур добавлен безопасный `web fallback` для factual-вопросов, которых нет в vault: только через официальные или первичные источники, без форумов и отзывиков.
- Исправлен salary-ответ по `Тетрике`: bridge больше не уводит в анкету с фразой `в анкете всё увидите`, а отвечает из базы `50–70 тыс. + доплата новичкам`.
- Добавлена утилита `tools/reset_hermes_chat_state.py` для сброса памяти Hermes по конкретному чату или полностью по всему `chat_state.json`, чтобы можно было начинать диалог заново без ручного редактирования state-файла.
- В live-bridge добавлена chat-команда `/clear` (`/reset` тоже поддерживается): она сбрасывает память по текущему диалогу, удаляет learning-note по этому чату и отвечает в переписке `Диалог очищен. Можем начать заново.`
- Исправлена ветка `расскажите подробнее`: теперь на стадиях `offered/qualified` bridge отдаёт отдельный подробный ответ по вакансии, а не повторяет один и тот же короткий оффер. Заодно усилен матчинг региона для живых формулировок вроде `в Челябинской области`.
- Переписан старт квалификации в более живой тон: bridge больше не начинает диалог с фразы `Да, актуально`, а пишет как живой рекрутер `Здравствуйте. Чтобы понять, какой вариант Вам лучше подойдёт, коротко уточню...`
- Исправлен парсинг многострочного ответа `Опыт есть`: теперь bridge распознаёт его как наличие опыта и не повторяет один и тот же вопрос. Для реплик уровня `я же написал` добавлена защита от повторного запроса того же пункта.
- Усилен парсинг коротких ответов по строкам `Был / Да / от 6 часов / Оператор чата / Волгоград`: bridge теперь понимает такой формат как полноценную анкету, не записывает `Был` в город и не зависает на повторе первого вопроса.
- Исправлена qualification-формулировка по технике: bridge и recruiter-vault больше не обещают, что компания обеспечит оборудованием; канон закреплён как `свой ПК/ноутбук и стабильный интернет`, если карточка вакансии не говорит иное.
- Генерация recruiter-ответа переведена в режим `Hermes-first`: Python-мост больше не ведёт стадии `new / qualifying / qualified / offered` жёсткими шаблонами и не повторяет опрос вместо Hermes.
- Deterministic-слой оставлен только для служебных и операционных кейсов: `ты бот?`, ограничение `только чаты/без звонков`, late-contact objection, post-form сопровождение, `waiting_form/done` и отправка анкеты после явного согласия.
- В контекст Hermes добавлен более жёсткий state brief: какие ответы уже есть, чего не хватает, и прямой запрет повторно задавать уже отвеченные вопросы.

## 2026-06-11

- Локальный workspace `TrafServer` очищен от helper-скриптов в корне: утилиты перенесены в `tools/`, ключ `codex_login_ed25519.strict` перенесён в `.ssh/`.
- Удалён локальный `tools/__pycache__`, чтобы vault не копил лишний runtime-мусор.
- Добавлен постоянный wiki-регламент `03 Плейбуки/Documentation synchronization contract.md` с правилами engineering investigation и documentation synchronization.
- Обновлены `README.md`, `Debugging.md` и связанные wiki-страницы под новую структуру vault.
- Серверный репозиторий `/root/TrafficHub` синхронизирован по документации: обновлены `README.md`, `wiki/*`, добавлены `docs/architecture.md`, `docs/api.md`, `docs/deployment.md`, создан `CHANGELOG.md`, изменения отправлены на GitHub отдельным docs-only commit через временный worktree.

## 2026-06-10

- Исправлена выдача `/api/logs`: теперь для `user` она читает owner-scoped persistent `app_log` и дополняется live `ws_manager`-историей.
- Исправлена кнопка очистки логов: теперь очищается и in-memory кэш, и persistent `app_log`.
- Зафиксирован root cause, при котором пользователь видел только старт запуска, хотя `traffichub_worker` уже писал полный цикл в persistent history.

## 2026-06-08

- Упрощена live-схема контейнеров TrafficHub: удалена лишняя `account_manager_net`, оставлены `core_net` и `edge_net`.
- `license_auth` отвязан от общего `data`, `account_manager` отвязан от общих `secrets`.
- Добавлен heartbeat-healthcheck для `traffichub_worker`.
- Runtime-secrets вынесены из `secrets/` в `data/runtime/secrets/`; системные ключи и identity-файлы оставлены в `secrets/`.
- `worker` переведён на read-only mount системного `secrets/`.
- Синхронизирован `remote_server_snapshot` по актуальным server-side файлам: compose, worker, config settings.
- Обновлены `README.md`, `docs/architecture.md`, `docs/deployment.md` под фактическое состояние live-сервера и runtime-layout.

## 2026-06-03

- Создан корневой `README.md` с каноническим описанием workspace и целевой системы.
- Добавлены `docs/architecture.md`, `docs/api.md`, `docs/deployment.md`.
- Создан набор страниц Obsidian wiki в `02 Архитектура`, `03 Плейбуки`, `04 Сущности`.
- Добавлен аудит расхождений между кодом и старой документацией.
- Зафиксированы архитектурные решения и ограничения по неполному snapshot.

## 2026-06-04

- Для `remote_server_snapshot/AccountManager` собран backend scaffold: `config`, `database`, `services`, `api/routers`, `dashboard`.
- Добавлены API-контракты для `/api/telegram/*`, `/api/google/*`, `/api/social/*`, а также базовые `/api/proxies/*`, `/api/dashboard/*`, `/api/accounts`.
- `AccountManager/api/main.py` подключён к новым роутерам.
- Обновлены README, architecture/api docs и wiki-страницы под текущее состояние AccountManager.
- Добавлены frontend assets `dashboard/css/*`, `dashboard/js/*`.
- Добавлен `chrome-extension/*` для Google cookie export flow.
- Добавлен `scheduler.py` и smoke-проверка `tests_smoke.py`.
# 2026-06-07

- Переведён `control_store` на PostgreSQL-first runtime backend.
- Полностью мигрированы legacy-таблицы `control.db` в `control_*` таблицы PostgreSQL.
- Добавлен one-shot режим legacy import, чтобы старый `control.db` не перетирал новые данные после миграции.
- `/api/health` теперь показывает backend control store и флаг `legacy_import_enabled`.
