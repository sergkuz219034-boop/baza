# HR Архитектор — генератор креативов

## Назначение

Отдельный workspace Account Manager для генерации текстов вакансий через OpenRouter. Не является частью `Telegram HR Agent`.

## Точки входа

- UI: `/root/TrafficHub/AccountManager/dashboard/index.html`, `data-tab="hr-architect"`.
- Frontend: `/root/TrafficHub/AccountManager/dashboard/app.js::generateHrCreatives()`.
- API: `POST /api/hr-architect/generate`.
- Router: `/root/TrafficHub/AccountManager/api/routers/hr_architect.py`.

## Контракт

Вход:

- вакансия;
- целевая аудитория;
- только подтверждённые условия и преимущества;
- канал: Telegram, VK, Avito, hh.ru или универсальный;
- тон: дружелюбный, экспертный, энергичный или лаконичный;
- цель и количество вариантов от 1 до 5.

Выход каждого варианта:

- `title`;
- `text`;
- `cta`;
- `short_text`.

## OpenRouter

- Credential: env `OPENROUTER_API_KEY`, только server-side.
- Model env: `HR_ARCHITECT_OPENROUTER_MODEL`.
- Default model: `openai/gpt-4.1-mini`.
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`.
- JSON response обязателен; пустой/невалидный ответ возвращает `502`.

## Безопасность и хранение

- Endpoint требует `request.state.username`, установленный auth middleware Account Manager.
- Ключ не попадает в HTML/JS/API response.
- Промт запрещает выдумывать зарплату, график, оформление и обязанности, но результат всё равно требует человеческой проверки перед публикацией.
- Вход и результаты не сохраняются в БД; история существует только в текущем DOM до перезагрузки страницы.

## Связи

- [[01_Расследования/2026-07-16 AccountManager вкладка HR Архитектор]]
- [[01_Расследования/2026-07-15 Telegram HR Agent и Business аккаунты]]
