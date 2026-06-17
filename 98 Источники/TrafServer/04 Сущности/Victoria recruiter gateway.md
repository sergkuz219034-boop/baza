# Victoria recruiter gateway

Теги: #сущность

## Назначение

`victoria-recruiter-gateway.service` даёт Hermes Workspace HTTP-backend, совместимый с OpenAI API.

Он нужен для server-side dashboard/chat в `https://am.traffic-hubcrm.ru/hermes/`.

## Runtime-факты

- systemd unit: `victoria-recruiter-gateway.service`
- listen: `127.0.0.1:8642`
- код: `/home/codex/hermes-user-bridge/recruiter_workspace_gateway.py`
- локальный исходник: `tools/recruiter_workspace_gateway.py`
- Python: `/usr/local/lib/hermes-agent/venv/bin/python`
- recruiter brain: `/home/codex/hermes-user-bridge/hermes_telegram_user_bridge.py`
- vault: `/home/codex/obsidian/hermes-victoria-vault`

## API

- `GET /health`
- `GET /v1/models`
- `GET /v1/chat/completions`
- `POST /v1/chat/completions`

`POST /v1/chat/completions` принимает OpenAI-style `messages[]`, выделяет пользовательский текст и вызывает `_ask_hermes(...)` из recruiter bridge. Состояние dashboard-чата хранится отдельно в `/home/codex/.hermes_user_bridge/workspace_chat_state.json`.

## Граница ответственности

Этот gateway не читает Telegram и не отправляет сообщения кандидатам. Telegram-отработка Виктории остаётся в отдельном процессе `hermes_telegram_user_bridge.py`.

Gateway нужен только для Workspace UI, чтобы оператор мог общаться с тем же Hermes/Victoria brain через dashboard.

## Проверка

- `systemctl status victoria-recruiter-gateway.service`
- `curl http://127.0.0.1:8642/health`
- `curl https://am.traffic-hubcrm.ru/hermes/api/gateway-status`
- `curl https://am.traffic-hubcrm.ru/hermes/api/claude-proxy/v1/chat/completions`

## Смежные страницы

- [[Deployment]]
- [[Hermes Workspace live publish]]
- [[Hermes Telegram bridge deployment]]
