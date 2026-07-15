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
