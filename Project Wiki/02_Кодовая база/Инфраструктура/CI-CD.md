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
