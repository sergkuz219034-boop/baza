# HR Agent LLM-first и серверные действия

## Проблема

Детерминированная sales-машина подменяла смысл диалога ключевыми словами, повторяла вопросы и не использовала LLM как основной мозг.

## Контекст

Входящие Telegram/Business updates обрабатывает [[Telegram Business сообщения обрабатываются через общий HR webhook]]. Каталог вакансий и кандидатские данные tenant/owner-scoped.

## Решение

- `traffic_hub/hr_agent/agent.py` — единственный первичный планировщик ответа через OpenRouter, строгий JSON: `reply`, `actions`, `handoff_required`, `conversation_state`.
- `traffic_hub/hr_agent/tools.py` — allow-list серверных действий. Модель не получает и не формирует ссылки анкет; URL ищется по активной owner/tenant вакансии.
- `policy.py` останавливает автоматизацию на stop-сигналах и блокирует чувствительные данные; `validator.py` проверяет повторы, URL и небезопасный текст. Одна повторная попытка LLM допустима, далее короткий handoff.
- `automation_mode` (`bot`, `human`, `paused`, `approval_required`) хранится у кандидата и диалога. AccountManager interceptor изменяет его в PostgreSQL и отменяет pending touches.
- AccountManager показывает/сохраняет OpenRouter status, модель, вариативность/temperature и лимит ответа.

## Последствия

- `sales_engine` больше не вызывается в основном входящем диалоге.
- Дожимы проходят тем же LLM-agent, но scheduler остаётся серверным и ограничивает их количество.
- Для существующих production БД миграция 0011 аддитивна; см. [[HR Agent: переход на LLM-first]].

## Альтернативы

Оставить шаблонную sales-машину и применять LLM только для перефразирования. Отклонено: она не решает проблему понимания контекста и приводит к повторным вопросам.
