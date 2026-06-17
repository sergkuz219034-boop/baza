---
tags: [provider, cloud, alibaba, dashscope]
updated: 2026-04-20
sources: [mcp_config.json, qwen-docs]
---
# Alibaba DashScope (Official Qwen API)

> Официальный облачный API от Alibaba Cloud для доступа к семейству моделей Qwen.

## Конфигурация в Antigravity
- **MCP Сервер**: `@modelcontextprotocol/server-openai`
- **Base URL**: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- **Статус**: Ключ валиден, ожидается активация моделей в консоли.

## Доступные модели (на 20.04.2026)
- `qwen3.6-max-preview`
- `qwen3.6-35b-a3b`
- `qwen3.6-flash`
- `qwen3.5-omni-plus-realtime`

## Заметки по настройке
Ключ успешно прошел проверку подлинности на международном эндпоинте DashScope. Если возникает ошибка `Model access denied`, необходимо активировать нужные модели в панели управления [Alibaba Cloud Model Studio](https://home.qwencloud.com/).

## Связанные страницы
- [[entities/qwen-hybrid|entities/qwen]] — используемая модель.
- [[synthesis/synthesis|index]] — главный индекс.
