# 2026-06-28 Research workflow для дебага и разработки

## Симптом

- В TrafficHub часто повторяются одни и те же классы проблем: regressions после UI/backend фиксов, неполная проверка user-contour, дрейф live/runtime, возврат старых ошибок.
- Нужен workflow, который подходит не для абстрактного проекта, а для server-first SaaS с live runtime, worker, scheduler, внешними интеграциями и canonical wiki.

## Зона системы

- Engineering workflow.
- Debug/incident response.
- Deploy verification.
- Wiki as engineering memory.

## Гипотеза

- Текущий workflow в целом правильный, но слишком линейный.
- Для TrafficHub нужны два режима:
  - обычная разработка;
  - incident/debug mode с working log, mitigation, rollback и postmortem.

## Проверка

Проверены внешние источники:

- Google SRE: incident response должен иметь понятные роли, working record, раннее объявление incident и постоянную запись debugging/mitigation.
  - https://sre.google/workbook/incident-response/
  - https://sre.google/sre-book/managing-incidents/
- Atlassian: postmortem должен быть blameless, reviewed и превращаться в процессные улучшения, иначе инцидент фактически не закрыт.
  - https://www.atlassian.com/incident-management/postmortem
  - https://www.atlassian.com/incident-management/handbook/postmortems
- Martin Fowler: deployment pipeline должен давать быстрый feedback после commit; trunk/main должен оставаться deployable.
  - https://martinfowler.com/articles/continuousIntegration.html
- Martin Fowler feature toggles: incomplete/risky behavior можно держать в production как latent code, но включать через toggles.
  - https://martinfowler.com/articles/feature-toggles.html
- GitHub Docs: required status checks нужны как gate перед merge/deploy.
  - https://docs.github.com/articles/about-status-checks
  - https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches

## Наблюдение

TrafficHub уже имеет сильные элементы workflow:

- live source of truth: `/root/TrafficHub`;
- wiki source of truth: local `wiki` + GitHub `baza`;
- server-first deploy;
- GitHub checks;
- runtime health;
- owner/user isolation as обязательный invariant;
- wiki investigation template.

Но отсутствуют или недостаточно жёстко закреплены:

- severity/risk gate перед началом работы;
- distinction между normal development и incident/debug;
- explicit mitigation before root-cause fix для user-facing incidents;
- short rollback plan before live deploy;
- artifact checklist: logs, screenshots, DB read-only query, affected owners;
- postmortem/review rule для повторяющихся ошибок;
- “definition of done” отдельно для UI, backend, scheduler, integrations.

## Вывод

Лучший workflow для TrafficHub:

1. `Classify` — определить тип задачи и риск.
2. `Stabilize` — если user-facing incident, сначала снизить вред: техработы, toggle, stop worker, disable offer/scheduler.
3. `Observe` — собрать факты: logs, runtime state, DB read-only, affected owner, container, commit.
4. `Localize` — найти конкретный файл/function/table/endpoint.
5. `Fix root cause` — минимальный фикс, не workaround в UI.
6. `Prove` — тест + runtime probe + multi-owner smoke.
7. `Ship` — commit, push, GitHub checks, rebuild/recreate, health.
8. `Document` — wiki investigation, catalog update, sync `baza`.
9. `Review` — если ошибка повторялась, добавить guardrail/test/runbook.

## Рекомендуемый режим для TrafficHub

### Normal development

- Подходит для UI polish, docs, small features, non-risky fixes.
- Не требует техработ, если не меняет live data/worker/auth.
- Обязателен post-deploy smoke по затронутому UI/API.

### Debug / incident mode

- Включается при user-facing broken flow, auth/settings leak, scheduler/worker bug, data corruption risk, external integration failure.
- Требует working note в `01_Расследования`.
- Для рискованных live-проверок включать техработы.
- Сначала mitigation, потом root cause.
- Закрывается только после wiki update и regression guard.

### Architecture / refactor mode

- Начинается с graphify/fallback architecture scan.
- Изменения дробить на small commits.
- Обязательно фиксировать architecture decision в `05 Решения`.

## Следующий шаг

- Обновить `[[01_Правила/ИИ/Workflow Codex для дебага и разработки]]` до модели `Classify → Stabilize → Observe → Localize → Fix → Prove → Ship → Document → Review`.
- Для повторяющихся багов добавить обязательный regression guard: test, static check, smoke script или runbook check.
