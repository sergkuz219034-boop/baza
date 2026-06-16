# 2026-06-16 Live check TrafficHub подтвердил новый HEAD и сломанный agent SSH config path

## Симптом

- после перестройки `baza` нужно было проверить не snapshot, а реальный live `TrafficHub`;
- одновременно требовалось убедиться, что канонический agent SSH path действительно работает из текущего workspace.

## Зона системы

- live host `150.241.70.31`;
- `/root/TrafficHub`;
- локальный agent SSH config `.codex_ssh/config`.

## Гипотеза

Если выполнить live SSH smoke и минимальный runtime audit, то:

- можно сверить текущий `HEAD` и container state с устаревшим snapshot;
- можно отделить server truth от старых локальных заметок;
- можно поймать локальные проблемы доступа к ключу, если они снова появились.

## Проверка

Подтверждено live `2026-06-16`:

- прямой SSH по ключу:
  - `ssh -i ...codex_login_ed25519.current codex@150.241.70.31`
  - отвечает `ok / codex / TrafficHub.play2go.cloud`
- repo:
  - `/root/TrafficHub`
  - `HEAD = a8f0be217fc7f23b8af6dead50b9968c9620cea1`
- live dirty files:
  - `AccountManager/dashboard/app.js`
  - `AccountManager/dashboard/index.html`
- health:
  - `{"status":"ok","version":"1.2","app":"TrafficHub","control":{"backend":"postgres","legacy_import_enabled":false,"ok":true}}`
- live container contour:
  - `traffichub_account_manager`
  - `traffichub_worker`
  - `autolead_server_bot`
  - `traffichub_caddy`
  - `traffichub_license_server`
  - `traffichub_license_auth`
  - `traffichub_postgres`
  - `traffichub_redis`
- live `docker-compose.yml` подтверждает:
  - `CONTROL_PG_LEGACY_IMPORT=false`
  - `WORKER_MAX_PARALLEL_OWNERS=2`
- live `api/server.py` подтверждает:
  - `register_traffic_hub(app)`
  - `GET /api/account-manager/token`
  - `GET /api/health`
  - `WS /ws/log`
  - `WS /ws/status`
  - cookie `traffichub_session`
- live `traffic_hub/app.py` монтирует:
  - `auth`
  - `integrations`
  - `leads`
  - `offers`
  - `finance`
  - `messengers`
  - `funnels`
  - `tracking`
  - `postbacks`
  - `stats`
  - `tools`
- worker heartbeat свежий:
  - `/app/data/runtime/worker.heartbeat`
  - `alive:2026-06-16T19:32:17.734452+00:00`
- worker/web logs подтверждают:
  - PostgreSQL runtime initialized для logs/delivery/leads/autofit_seen/invites/control_sync_queue
  - hourly `partner_sync` для `audit-admin`

Отдельно подтверждено локально:

- `.codex_ssh/config` ссылался на несуществующий absolute path без сегмента `Project`;
- из-за этого `ssh -F ...` падал с `no such identity`;
- после исправления `IdentityFile` repo-local agent config снова стал рабочим.

## Наблюдение

- старый snapshot уже устарел по `HEAD`:
  - было `b1c252e...`
  - live сейчас `a8f0be2...`
- server truth остался согласован с каноном по PostgreSQL control/runtime и worker parallelism;
- проблема с agent SSH на этот раз была не ACL, а устаревший absolute path в config.

## Вывод

- live `TrafficHub` сейчас здоров и доступен;
- локальные wiki нужно синхронизировать уже от `a8f0be2...`, а не от старого snapshot;
- канонический agent SSH path надо держать не только по ACL, но и по актуальному workspace path.

## Следующий шаг

- обновить `server-snapshot.md`, `server-ssh-access.md` и канонический `Project Wiki`;
- при следующих live-check сначала делать `ssh -F ... "echo ok && whoami && hostname"`;
- при расхождении snapshot/live всегда предпочитать live.
