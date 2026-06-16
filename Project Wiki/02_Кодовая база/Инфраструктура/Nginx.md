# Nginx

## Статус

Подтверждённый reverse proxy в проекте — `Caddy`, а не `Nginx`.

## Для чего страница нужна

- фиксировать это расхождение явно;
- не допускать ложной документации “по умолчанию” про Nginx.

## Что реально используется

- edge reverse proxy: `traffichub_caddy`;
- публичные домены:
  - `traffic-hubcrm.ru`
  - `auth.traffic-hubcrm.ru`
  - `am.traffic-hubcrm.ru`

## Следствие

- если кто-то пишет инструкцию "проверь nginx", это нужно сначала перепроверить по live host;
- TLS/upstream/edge routing проблемы искать в Caddy, а не в Nginx.

## Глубокие ссылки

- [[Project Wiki/raw/docs/TrafficHub-obsidian/04 Сущности/Контейнеры и сервисы|Контейнеры и сервисы]]
