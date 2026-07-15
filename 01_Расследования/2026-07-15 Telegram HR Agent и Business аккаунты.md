# Telegram HR Agent и Business-аккаунты

## Симптом

`Telegram HR Agent` выглядит настроенным, но не автоматизирует личные чаты подключённых Telegram-аккаунтов.

## Зона системы

- `/root/TrafficHub/hr_ai_worker/main.py`
- `/root/TrafficHub/traffic_hub/hr_agent/service.py`
- `/root/TrafficHub/AccountManager/api/routers/hr_agent.py`
- таблицы `telegram_accounts`, `hr_agent_channel_bindings`, `hr_agent_candidates`, `hr_agent_messages`
- контейнеры `traffichub_app`, `traffichub_hr_ai_worker`
- [[05_Решения/Telegram Business сообщения обрабатываются через общий HR webhook]]

## Гипотеза

Бот исправен, но ни один Telegram Business-аккаунт не подключил его к личным чатам; отдельный Telethon-worker ошибочно воспринимается как основной runtime.

## Проверка

- Проверены live `getMe` и `getWebhookInfo` без вывода токена.
- Проверены подписанные update-типы, очередь и последняя ошибка webhook.
- Сверены код `hr_ai_worker`, AccountManager, HR webhook и фактические строки PostgreSQL.
- Добавлен regression-test на событие `business_connection`.
- Выполнены commit/push, GitHub checks, rebuild `autolead_bot`, public health и synthetic webhook smoke.

## Наблюдение

- `@Vectoria101_bot` валиден и имеет `can_connect_to_business=true`.
- Webhook указывает на `https://traffic-hub.pro/traffic-api/hr/webhooks/telegram`; очередь равна нулю, последней ошибки нет.
- Подписка включает `business_connection`, `business_message`, `edited_business_message`, `deleted_business_messages`.
- До фикса в `hr_agent_channel_bindings.extra_config` не сохранялись события подключения Business-аккаунта. Поэтому система не различала состояния «webhook исправен» и «аккаунт подключён».
- В live есть пять активных `telegram_accounts`, но `hr_ai_worker/main.py` ищет только Викторию, не расшифровывает AccountManager session и пишет HR-данные жёстко в `tenant_id=1`, `owner_username=admin`. Это legacy-прототип, не канон multi-account automation.
- Commit `39ec17913` сохраняет enabled/disabled Business connections в owner-scoped binding `extra_config.business_connections`.
- Regression: `tests/test_hr_agent_router.py`, `2 passed`; CI, Extended checks и Docker build успешны.
- После deploy `traffichub_app` healthy, `/api/health` возвращает `status=ok`, synthetic Business-event обработан новым кодом.

## Вывод

Канонический контур автоматизации личных чатов — Telegram Bot API Business webhook. Один HR-бот может получать отдельные `business_connection_id` от подключённых Business-аккаунтов и отвечать от имени соответствующего аккаунта. Серверная часть исправна и теперь фиксирует подключения. Ни одного реального Business connection на момент проверки не было; подключение каждого аккаунта подтверждается владельцем в Telegram и не может быть создано сервером без этого действия.

`hr_ai_worker` не является полноценной альтернативой и требует отдельного ADR/переработки либо удаления из production compose.

## Следующий шаг

На нужном Telegram-аккаунте открыть `Настройки → Telegram Business → Чат-боты`, подключить `@Vectoria101_bot`, разрешить управление личными чатами и отправить тестовое входящее сообщение с другого аккаунта. После update `business_connection` проверить `extra_config.business_connections`, создание owner-scoped кандидата и исходящий ответ с тем же `business_connection_id`.

## Дополнение: системный промт каждого бота

- Commit `b369dea66` добавил поле `Системный промт` в create/edit modal `AccountManager/dashboard/index.html`.
- Значение хранится в `HrAgentChannelBinding.extra_config.system_prompt`, поэтому принадлежит конкретному owner-scoped bot binding, а не общему `HrAgentConfig`.
- `AccountManager/api/routers/hr_agent.py::_binding_extra_config()` ограничивает промт 12 000 символами и не разрешает UI перезаписать внутренний `extra_config.business_connections`.
- `traffic_hub/hr_agent/service.py::_llm_response()` получает текущий binding и добавляет только его промт в защищённую системную обвязку этапа воронки и JSON-контракта.
- Regression проверяет отсутствие смешивания `PROMPT-ALPHA` и `PROMPT-BETA` между двумя binding.
- Live `hr_agent_configs` для `admin` переведён на `provider=openrouter`, `model=openrouter/free`, `enabled=true`; API key не хранится в БД и читается из `OPENROUTER_API_KEY` контейнера.
- Проверены GitHub CI/Extended/Docker build, health `traffichub_app` и `traffichub_account_manager`, публичный cache-busted asset и ответ OpenRouter.

## Связанные заметки

- [[05_Решения/Telegram Business сообщения обрабатываются через общий HR webhook]]
- [[05_Решения/Telegram HR бот подключается по названию и токену]]
- [[05_Решения/Системный промт HR Agent принадлежит binding бота]]
- [[05_Эксплуатация/Развёртывание]]

## Дополнение: естественный темп ответа

- Telegram Bot API показывает статус `typing` через `sendChatAction`; статус действует не более пяти секунд и исчезает при отправке сообщения.
- Commit `3765f4178` отправляет `typing` до обращения к LLM и обновляет его каждые четыре секунды, пока формируется ответ.
- Для Business-чата в `sendChatAction` передаётся тот же `business_connection_id`, что и в последующий `sendMessage`; это проверено на live через сохранённую реальную Business-сессию без вывода токена и персональных данных.
- После генерации применяется ограниченная задержка `0,8–4,0` секунды, зависящая от длины текста и небольшого jitter. Предел защищает webhook от чрезмерно долгого удержания запроса.
- Ошибка chat action логируется как warning и не блокирует доставку ответа кандидату.
- Regression-набор `tests/test_hr_agent_router.py` и `tests/test_account_manager_hr_prompt.py`: `7 passed`; GitHub CI, Extended checks и Docker build успешны.
- После rebuild `traffichub_app` healthy, публичный `/api/health` возвращает `status=ok`, live smoke `sendChatAction` вернул `ok`.

## Дополнение: отметка прочтения

- Telegram Bot API предоставляет `readBusinessMessage` для входящих Business-сообщений; запрос требует `business_connection_id`, `chat_id` и `message_id`.
- Commit `16fe24448` сохраняет `message_id` при разборе webhook и вызывает отметку прочтения после записи входящего сообщения, до статуса `typing`.
- Метод вызывается только для `business_message`: обычная переписка непосредственно с ботом не имеет Business connection и не имитирует receipt.
- Ошибка Telegram API логируется как warning и не блокирует генерацию или доставку ответа.
- Regression-набор: `7 passed`; GitHub CI, Extended checks и Docker build успешны.
- После deploy `traffichub_app` healthy, `/api/health` возвращает `status=ok`; live smoke на сохранённом реальном Business-сообщении вернул `ok`.

## Дополнение: повтор fallback вместо ответа на вопрос

### Симптом

На сообщения `привет` и `расскажите о вакансии` агент дважды отправил одну фразу о возможности ответить на вопросы и вернуться к анкете.

### Проверка

- В `hr_agent_messages` у проблемных исходящих сообщений `llm_model` был пустым: системный промт не формировал финальную реплику.
- Live-логи показали `200 OK` OpenRouter, после которого парсер падал на обычном тексте и JSON `null`; позднее `openrouter/free` вернул `429 Too Many Requests`.
- Стабильная модель `openai/gpt-4.1-mini` на том же env credential отвечает успешно.
- Пользовательский промт содержал абсолютное правило `Всегда начинай диалог`, конфликтующее с текущим этапом `form_offer` и прямым вопросом кандидата.
- В таблице нет активных `hr_agent_vacancies`, а `default_vacancy_id` binding равен `NULL`; факты о вакансии пока берутся из bot-specific system prompt.

### Вывод

Проблема была составной: нестабильный free-router, слишком строгий JSON-парсер и конфликт сценарного промта. Повтор fallback не является качеством LLM-ответа, потому что LLM-ответ отбрасывался полностью.

### Исправление

- Commit `eb39bdc1a` принимает JSON, fenced JSON и обычный текст, отклоняя пустой/`null` результат.
- Защищённая обвязка делает прямой ответ на последнее сообщение приоритетнее перезапуска приветствия и передаёт предыдущие реплики кандидата и рекрутера.
- Live binding `HR Виктория` получил правило не повторять ответ и отвечать на вопрос о вакансии; приветствие ограничено этапом `greeting`.
- Live model переключена с `openrouter/free` на `openai/gpt-4.1-mini`; credential остаётся только в env.
- Regression: `8 passed`; полный GitHub CI, Extended checks и Docker build успешны после test-only commit `c3b6999d5`.
- После deploy `traffichub_app` healthy, `/api/health` возвращает `status=ok`. Live-smoke на сохранённом вопросе предложил актуальную удалённую вакансию и доход `50 000–70 000` вместо fallback.

### Следующий шаг

Создать owner-scoped запись `hr_agent_vacancies` и назначить её `default_vacancy_id`, чтобы условия вакансии были структурированными данными, а не только частью длинного промта.

## Дополнение: температура каждого бота

- Commit `51ed7d2c4` добавил в create/edit modal ползунок `Вариативность ответов` от `0,0` до `2,0` с шагом `0,1`.
- Значение сохраняется в owner-scoped `extra_config.temperature` конкретного Telegram binding и передаётся в OpenAI-compatible payload.
- API валидирует диапазон и сохраняет внутренние `business_connections`; существующему live binding `HR Виктория` записано значение `0,4`.
- Regression: `10 passed`; GitHub CI, Extended checks и Docker build успешны.
- После deploy `traffichub_app` и `traffichub_account_manager` healthy, `/api/health` возвращает `status=ok`; новый UI и runtime подтверждены внутри live-образов.

## Дополнение: Markdown-база знаний

- Commit `3207c7720` добавил `extra_config.knowledge_base_md`, API-лимит 30 000 символов, textarea и загрузку `.md` в create/edit modal.
- Runtime передаёт Markdown только в system context текущего binding; regression проверяет отсутствие смешивания `KB-ALPHA` и `KB-BETA`.
- Product template `/root/TrafficHub/docs/templates/hr_recruiter_knowledge_base.md` содержит 195 строк: вопросы, квалификацию, возражения, анкету, касания 24/72 часа, повторы и стоп-сигналы.
- В live binding `HR Виктория` загружено 6 987 символов шаблона. Контрольное возражение обработано уточняющим вопросом без давления и повторной анкеты.
- Regression: `14 passed`; GitHub CI, Extended checks и Docker build успешны.
- После deploy оба контейнера healthy, `/api/health` возвращает `status=ok`.

Связано: [[04 Сущности/HR Agent Markdown база знаний]]

## Аудит применения промта и базы знаний 2026-07-15

### Проверка

- Live binding `HR Виктория` активен: системный промт `4 701` символ, Markdown-база `6 987` символов, температура `0,4`.
- LLM config: `provider=openrouter`, `model=openai/gpt-4.1-mini`, `enabled=true`; credential присутствует только в env.
- Код `traffic_hub/hr_agent/service.py::_llm_response()` добавляет `knowledge_base_md` и `system_prompt` текущего binding в system message и сохраняет использованную модель в исходящем `hr_agent_messages.llm_model`.
- За 72 часа в `hr_agent_messages` записано `26` сообщений: `12` входящих, `14` исходящих; у `5` исходящих подтверждена LLM-модель, остальные были fallback.
- Изолированный LLM-smoke без отправки в Telegram на вопрос об обязанностях, графике и зарплате вернул `openai/gpt-4.1-mini` и факты из системного промта: Тетрика, удалённый формат, `50 000–70 000`, графики `5/2` или `2/2`, звонки через автообзвон.

### Наблюдение

- Промт и Markdown-база технически подключены и реально попадают в LLM-контекст.
- Следование инструкциям нестабильно: последние реальные ответы на `привет` в стадии `form_offer` повторно начинали знакомство, хотя protected wrapper, bot prompt и база запрещают повторное приветствие после первого контакта.
- В базе нет активных `hr_agent_vacancies`; `default_vacancy_id` binding равен `NULL`.
- Источники знаний противоречат друг другу: Markdown-база помечает точные обязанности и график неизвестными, системный промт задаёт их явно. Модель выбрала факты системного промта, но при таком конфликте результат недетерминирован.
- У binding нет сохранённых активных `business_connections`; проверенные сообщения относятся к прямому Telegram bot chat, а не к ответам от имени Business-аккаунта.

### Вывод

HR Agent технически работает через заданный системный промт и Markdown-базу, но пока нельзя считать его поведение полностью корректным. Основные причины: конфликт фактов между двумя источниками, отсутствие структурированной вакансии и заметная доля fallback-ответов.

### Следующий шаг

Сделать системный промт сценарным, а факты о вакансиях хранить в одном источнике: создать owner-scoped `hr_agent_vacancies`, назначить `default_vacancy_id` и убрать из Markdown-базы утверждение «график и обязанности неизвестны» для Тетрики. После этого прогнать сценарии первого сообщения, повторного приветствия, вопроса о вакансии, возражения и согласия на анкету.

## Комплексный фикс диалога 2026-07-15

### Симптом

- Фраза «расскажите о вакансии» не считалась вопросом без `?` и попадала в fallback текущей стадии.
- Из `22` исходящих за 7 дней только `5` имели подтверждённую LLM-модель; `17` были жёсткими fallback-репликами.
- `runtime_flags.llm_enabled=false` противоречил активному OpenRouter config, но код игнорировал флаг.
- В БД не было вакансий, `default_vacancy_id` был `NULL`, а Markdown-база противоречила системному промту по обязанностям и графику.
- Повторная доставка одного Telegram update могла сформировать второй ответ.

### Проверка

- Прослежены `traffic_hub/hr_agent/service.py`, webhook router, scheduler касаний и live PostgreSQL.
- Добавлены проверки естественных вопросительных форм, runtime-флага и duplicate Telegram message/update.
- Выполнен изолированный live LLM-smoke на стадиях `greeting`, `form_offer`, `questions` без отправки сообщений кандидатам.
- Проверены `getWebhookInfo`, public health и логи после пересоздания `traffichub_app`.

### Наблюдение

- Product commit `d9d2d2c3a` расширяет определение вопроса, учитывает `runtime_flags.llm_enabled`, передаёт структурированную вакансию как приоритетный источник фактов и отбрасывает повторный Telegram update по `_event_key`.
- Commit `e989ef9bd` устраняет конфликт фактов в шаблоне Markdown-базы.
- Создана owner-scoped вакансия `Менеджер на вводный урок — Тетрика`, назначена binding `HR Виктория`; `runtime_flags.llm_enabled=true`, база знаний `7 266` символов.
- Контрольный ответ на «расскажите о вакансии» содержит Тетрику, удалённый формат, задачи, доход, график и оформление без повторного приветствия.
- Ответ на «какой график и сколько платят?» содержит `5/2`/`2/2` и `50 000–70 000` с одним следующим вопросом.
- `17` целевых тестов, CI, Extended checks и Docker build зелёные; контейнер и `/api/health` healthy.
- Telegram webhook имеет `pending_update_count=0`, последней ошибки нет.

### Вывод

Подтверждённые программные и конфигурационные дефекты исправлены. Канонические факты вакансии теперь хранятся структурированно, а системный промт и Markdown управляют сценарием и стилем. Повторы webhook не порождают второй ответ.

### Следующий шаг

На live всё ещё нет реального `business_connection`: сервер не может создать его за владельца Telegram-аккаунта. Для ответов от имени аккаунта владелец должен подключить `@Vectoria101_bot` в Telegram Business и разрешить выбранные личные чаты. После первого события `business_connection` проверить сохранение connection id и выполнить end-to-end сообщение с другого аккаунта.
