# HR Архитектор — Creative Creator

Проверено 2026-10-11. В TrafficHub восстановлена вкладка «Автоматизация» (`#automation`) с Creative Creator, адаптированным из проекта hr-architect. Старый Content Bot в этой вкладке заменён.

## Точки входа

- UI: `/root/TrafficHub/dashboard/index.html`, `#tab-automation`.
- Frontend: `/root/TrafficHub/dashboard/app.js::generateCreative()`.
- Стили: `/root/TrafficHub/dashboard/creative-creator.css`.
- API: `POST /api/creative-creator/generate`, `/root/TrafficHub/api/routers/creative_creator.py`.

## Возможности

Рекламный креатив, вакансия, аудит текста, сравнение A/B. Бриф, аудитория, география, площадка, тон, цель и 1–5 вариантов. Для рекламы: угол, хук, заголовок, текст, короткая версия, CTA, идея визуала и сценарий видео. Это текстовый генератор; изображения и видео не создаются.

Промпт запрещает выдуманные условия, зарплаты, отзывы, скидки и гарантии. Аудит и A/B дают редакционные гипотезы, а не измеренные результаты кампании. Старые инструкции hr-architect по маскировке условий не перенесены.

## Провайдер и безопасность

По умолчанию используется настроенный серверный Codex Gateway, если есть его credential; иначе OpenRouter. `CREATIVE_CREATOR_PROVIDER` и `CREATIVE_CREATOR_MODEL` переопределяют выбор. Общий resolver `/root/TrafficHub/traffic_hub/hr_agent/providers.py`. Ответ ограничен 2000 токенами — контракт gateway; большие брифы/пять вариантов могут давать более краткий результат.

Требуется авторизованная роль user/admin; operator запрещён, анонимный запрос получает 401. Ключи только на сервере. Текст выводится через textContent. Бриф и результат не записываются в БД, сохраняются в текущем DOM до перезагрузки. Публикация вручную после проверки фактов.

## Доказательства

`C:/Users/admin/Desktop/Project/outputs/creative-creator-20261011/EVIDENCE.md`; сервер `/home/codex/creative-creator-20261011/`. 7 целевых тестов, реальные браузерные проверки тем и ширин 390/1440, живая генерация рекламного текста. Исходные резервные копии и app image.before в серверном evidence. Worker не перезапускался.