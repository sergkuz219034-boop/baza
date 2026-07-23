# HR Agent: Telethon unread, OpenRouter и анкеты

## Симптом

Виктория не читала непрочитанные личные диалоги Telethon; при `402` OpenRouter переходил на шаблонный fallback; описание и ссылка анкеты могли относиться к разным офферам.

## Зона системы

`AccountManager/services/hr_unread_worker.py`, `traffic_hub/hr_agent/agent.py`, `tools.py`, `service.py`, таблицы `hr_agent_*`.

## Гипотеза

Webhook обрабатывает только новые Bot API updates, а HR LLM использует одиночный env-ключ. URL был доступен LLM и не валидировался сервером по коду оффера.

## Проверка

Live AccountManager подключился к Telethon аккаунту и лог показал обработку unread. Первый запуск выявил `NameError: select`; после исправления worker подключается/отключается без traceback. Для личного диалога Bot API вернул `400`, поэтому delivery переведён на активный Telethon-клиент.

## Наблюдение

- Сканер каждые 20 секунд читает только personal inbound dialogs, исключая исходящие, группы, каналы и ботов.
- Telegram message ID становится event key, повторный poll/webhook не создаёт второй ответ.
- Ключи берутся из `OPENROUTER_API_KEY`, `OPENROUTER_API_KEYS` и `hr_agent_configs.llm_config.api_keys`; ошибка `401/402/429/5xx` переводит ключ в cooldown.
- URL берётся только из server map `offer_code -> URL`. Несоответствие блокирует отправку.

## Вывод

Контур HR остаётся в `account_manager`; `autolead_bot` не запускает HR runtime. Проверен live deploy `account_manager` на commit `a3dd802…`.

## Следующий шаг

В dashboard добавить редактор пула ключей без раскрытия секретов и провести ручной тест с новым непрочитанным личным сообщением @JobVictory.
