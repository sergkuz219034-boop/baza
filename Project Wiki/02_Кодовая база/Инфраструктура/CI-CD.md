# CI-CD

## Состояние

В `baza` нет подтверждённой детальной карты CI/CD pipeline.

## Что фиксировать сюда

- только реально подтверждённые deploy-пути;
- шаги публикации, если они проверены кодом, контейнерами или server-side артефактами.

## Уже подтверждённый deploy-risk

- после server-side правок нельзя считать runtime исправленным только по `autolead_server_bot`;
- нужно сверять image и код у:
  - `autolead_server_bot`
  - `traffichub_worker`

## Подтверждённый минимум

- проект деплоится контейнерно;
- runtime verification требует проверки `docker ps`, health и целевых логов;
- Windows launcher / installer существует как отдельный контур распространения, но не заменяет production deploy path.

## Что ещё нельзя утверждать

- в `baza` нет подтверждённой полной GitHub Actions/CI карты для production TrafficHub;
- старые Windows release notes не надо автоматически смешивать с server deploy.

## Глубокие ссылки

- [[Project Wiki/raw/docs/TrafficHub-obsidian/06-Deployment/Windows|Windows setup]]
- [[Project Wiki/raw/docs/TrafficHub-obsidian/04 Сущности/Контейнеры и сервисы|Контейнеры и сервисы]]
