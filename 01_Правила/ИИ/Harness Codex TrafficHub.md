# Harness Codex TrafficHub

Правила и bridge проверены: 2026-10-08. Harness — управляющий слой вокруг существующего TrafficHub, а не новый product runtime.

## Источники истины

1. Проверенные код, runtime и БД TrafficHub.
2. Эта Wiki — каноническое долговременное знание.
3. Архитектурные решения.
4. Agent-OS state текущей задачи.
5. Git.

RaytSystem является проекцией и панелью. Он не заменяет state, Wiki или Git и не получает полномочий менять product-код.

## Размещение и владение

- Product repo: `/root/TrafficHub`.
- Короткий вход агента: `/root/TrafficHub/AGENTS.md`.
- Подробные правила и циклы: `/root/TrafficHub/harness/`.
- Canonical task state: `/root/TrafficHub/state/{workstreams,receipts,handoffs,decisions,history}`.
- Curated memory: `/root/TrafficHub/memory/`.
- Project skills: `/root/TrafficHub/.agents/skills/`.
- Bridge и offline fallback: `/root/TrafficHub/tools/agent-os-bridge/`.
- Generated state, графы и проекции не коммитятся; versioned E2E evidence живёт только в `tools/agent-os-bridge/examples/`.

## Рабочий цикл и риск

`CLASSIFY → OBSERVE → LOCALIZE → PLAN → FIX → VERIFY → EVIDENCE → SHIP → DOCUMENT → REVIEW → CLOSED`.

`STABILIZE` обязателен перед risky mutation, если возможен impact. Классы риска: `READ_ONLY`, `LOW_RISK`, `RUNTIME_RISK`, `DATA_RISK`. Для runtime нужны stabilization и rollback evidence. Для data дополнительно фиксируются target, affected rows, backup/snapshot и dry run. Закрытие невозможно без task-scoped verify/evidence/review receipts и результата.

## Интеграции

- Agent-OS задаёт filesystem-first state, receipts и handoffs.
- Graphify — disposable навигационный граф, привязанный к exact source SHA; код остаётся доказательством.
- Headroom и Caveman уменьшают контекст и ответы, но не меняют canonical evidence.
- CodeBurn передаёт runs, tokens, cost, time, retries и outcomes.
- Ponytail проверяет лишние файлы, зависимости, дублирование, dead code и рост LOC; при отсутствии skill работает встроенный checklist.
- Текущая панель — RaytSystem, stateless loopback projection и governed-command client. Исторический Mission Control не использовать как текущий runtime-контур; актуальный release см. [[02_Код/Эксплуатация/RaytSystem Harness Control Center]].

Отсутствие любого optional tool не блокирует core workflow: capability получает статус `unavailable` или `degraded`, а доказательства продолжают храниться в Agent-OS.

## Runtime и безопасность

- Harness worktree никогда не подключается к live Compose.
- `/app` не редактируется.
- RaytSystem слушает только `127.0.0.1`; внешний доступ возможен только через управляемый SSH tunnel или отдельно согласованный authenticated TLS reverse proxy.
- Секреты, ПДн, полные логи, `.env`, backup и runtime data не входят в context, graph, receipts или Wiki.
- RaytSystem сохраняет lifecycle gates и не реализует mutation product-кода.

## Проверка и rollback

Core gate: targeted unittest, `py_compile`, JSON validation, dashboard browser smoke, `git diff --check`, independent validator. Runtime evidence: health TrafficHub и RaytSystem, актуальный immutable release и безопасный smoke lifecycle gates; maintenance не включать для обычной правки правил.

Rollback: переключить только RaytSystem на предыдущий immutable release и проверить health; продолжить по filesystem state; product harness откатывается отдельными Git-коммитами. Удаление canonical workstreams, receipts, handoffs или curated memory не является штатным rollback.

## Связанные правила

- [[Workflow Codex для дебага и разработки]]
- [[02_Код/Эксплуатация/Доступ и подключения]]
- [[01_Правила/Плейбуки/Graphify architecture scan]]

## Усиление proof — 2026-10-08

CLOSED требует привязку receipts к SHA-256 manifest фактических релевантных файлов и перечитывает их через proof_repo. Старые открытые задачи должны получить новую привязку и проверки; закрытые не мигрируются. Порядок стадий сохранён, неприменимые FIX/SHIP — no-op. Hash не аттестует запуск команд. Bridge в работающей панели импортируется из immutable release, поэтому обновление server repo должно сопровождаться выпуском панели. Доказательства: C:/Users/admin/Desktop/Project/outputs/harness-fix-20261008/.


