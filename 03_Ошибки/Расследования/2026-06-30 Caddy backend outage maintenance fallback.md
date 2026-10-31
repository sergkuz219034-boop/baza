# 2026-06-30 Caddy backend outage maintenance fallback

## Симптом

- Во время `docker compose up --build autolead_bot worker` пользователи могли видеть raw browser error или 502.
- В Caddy logs повторялось: `lookup autolead_bot on 127.0.0.11:53: no such host`.

## Зона системы

- `deploy/Caddyfile`
- Docker Compose service `autolead_bot`
- Caddy reverse proxy на `traffic-hub.pro`

## Гипотеза

- При пересоздании контейнера Docker на короткое время удаляет DNS alias `autolead_bot`.
- Caddy в этот момент не может резолвить upstream и отдаёт 502, хотя это нормальное deploy-window состояние.

## Проверка

- Live `docker compose ps` показал service `autolead_bot` с container name `traffichub_app`.
- `deploy/Caddyfile` проксировал public domain на `autolead_bot:8080`.
- Caddy logs за последние 6 часов содержали несколько `lookup autolead_bot ... no such host` на `/api/logs`, `/api/jobs/status`, `/ws/log`, `/ws/status`.
- App health при этом после deploy был OK.

## Наблюдение

- Это не business/runtime bug Autolead.
- Это инфраструктурный deploy-gap: backend контейнер здоров после старта, но во время recreate upstream alias временно отсутствует.

## Вывод

- Нельзя полагаться только на включение техработ в app, если сам app недоступен.
- Reverse proxy должен иметь fallback на уровне Caddy.

## Исправление

- Product commit: `746e7f483 fix: show maintenance page on backend outage`.
- В `deploy/Caddyfile` добавлен snippet `backend_unavailable_notice`.
- Для public domain `traffic-hub.pro` и legacy domain `traffic-hubcrm.ru` добавлен `handle_errors`, который отдаёт HTML-экран `Тех работы` при backend outage.

## Подтверждение

- `caddy validate --config /etc/caddy/Caddyfile`: valid.
- GitHub checks for commit `746e7f483`: `CI` success, `Build and Push Docker Image` success.
- `docker compose up -d caddy` применил конфиг.
- `https://traffic-hub.pro/api/health` вернул `status=ok`.
- После reload свежих Caddy `502/no such host/connect refused` в проверочном окне не найдено.

## Следующий шаг

- При будущих deploy больше не считать краткий backend restart пользовательским `ERR_CONNECTION_CLOSED`: пользователь должен видеть controlled maintenance page.
- Если 502 появляется не во время deploy, проверять уже `docker compose ps`, healthcheck app и Caddy upstream network.

## Дополнение 2026-10-12 — RU edge keepalive (H4)

Проверено по runtime: RU Caddy 2.11.4 отправляет запросы через TCP relay
`172.18.0.1:19580 → 127.0.0.1:19080 → origin:8080`. Сам reverse SSH tunnel
активен с 2026-10-09; в проверенном 36-часовом журнале не обнаружены его
перезапуски, но есть 48 отказов подключения к origin:8080. Это отдельный
признак временной недоступности приложения, а не доказательство потери SSH.

Прямой безопасный GET `/api/health` через tunnel подтвердил закрытие idle
HTTP-соединения upstream ровно через 5 секунд. В `main.py:226` нет override
`timeout_keep_alive`; runtime Uvicorn0.54.0 имеет default5. В RU Caddy не было
transport override. [Документация Caddy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy#the-http-transport)
задаёт default keepalive2m и объясняет риск 502 для неидемпотентных запросов,
если этот срок превышает timeout upstream. Это подтверждённое несогласование
конфигурации; оно не доказывает причину каждого из 2403 исторических 502.

В четырёх app reverse_proxy routes обоих TrafficHub domains установлен
`transport http { dial_timeout 10s; keepalive 2s }`. Проверены guard/idempotence
patch, синтаксис, Caddy validate, graceful reload и 8 GET health200 с idle
интервалами0/1/3/6 секунд. POST retry не добавлялся; приложения, workers,
SSH control relay и product container не перезапускались. TrafficHub server
commits `dea40b43035dbc29b9f9d55c1f313355183a5c15`,
`c2a8835891423fc519b1ef142e84e9dafc13b713`; версионированный patch
`/root/TrafficHub/deploy/ru-autolead/tune_edge_keepalive.py`.

Rollback всех изменений H4: на RU вернуть
`/opt/focus-group/Caddyfile.pre-high-tunnel-20261012` в `Caddyfile`, затем
Caddy validate/reload; прежде проверить, не внесли ли другие чаты более поздние
правки, и при их наличии откатить только transport blocks. Не делать blind
whole-file rollback поверх чужих изменений. Исходный SHA256
`5e7661dff4c83c6d16daef5221a5a8edb3ff193ded8813d10ce23e067507de4e`,
финальный SHA256 `c05cdd294ca0420a92753ba61ec22c335c257978e9aef00f3a74323a7b1acd2d`.

Доказательства: `C:/Users/admin/Desktop/Project/outputs/high-server-fixes-20261012/tunnel/`:
`keepalive.txt`, `detail.txt`, `apply.txt`, `apply-crm.txt`, `verify.txt`,
`commit.txt`, `commit-crm.txt`. Сводку длительного safe GET probe см. в
`final-probe.txt` после завершения. Исходная причина всех исторических EOF
и deploy-gap остаётся ограничением расследования; новые внешние отправки для
проверки не выполнялись.

Итог H4 live окна 2026-10-12: 08:13:55–08:23:56 UTC, 61/61 GET health200 за600.7s, max0.985s, новых Caddy5xx после reload нет. Все4 app transport blocks обоих доменов проверены: keepalive2s/dial timeout10s, retries не добавлены. Signed remote worker GEThealth успешен, unauth401. Доказательства: `C:/Users/admin/Desktop/Project/outputs/high-server-fixes-20261012/tunnel/final-probe.txt`, `verify-all.txt`, `queue-health.txt`.

## Проверка RU edge 2026-10-12 — LOW/HIGH продолжение

Свежие79HTTP50210:37:35–10:38:14UTC совпали с подтверждённой публикацией
MEDIUM app. После окна в30min новых5xx не обнаружено,12/12GET health200.
Не приписывать historical2403одной причине. Подготовлена futurecontrolled
maintenance503процедура безPOSTretry; неактивирована, zero-downtimeнеобещан.

Static sites иCRM опубликованы сnosniff/SAMEORIGIN/referrer policy;CRM HSTS.
Graceful Caddyvalidate/reload и6public200headers прошли. Backup
`/opt/focus-group/Caddyfile.pre-lowheaders-20261012`; послеhash
`82e257f03fa9779db946f2bb2ee9b718d7b6d010658125c1d3a9e8ddb993b5e4`.
RU4core source roots имеют whitelistGitbaseline/manifests;env/data/секреты
иfullCaddyисключены. Sourcehistory начинаетсясегодня, неотменяетbackup.

HHsignedGET/processread-onlymonitorактивен, ноactualconsumerDockerhealth
stagedimage ещёнеприменён до разрешённогоHHrecreate. НеобъявлятьL5полностью
закрытым. Evidence/точныеcommits/rollback:
`C:/Users/admin/Desktop/Project/outputs/low-high-server-fixes-20261012/ru/REPORT.md`,
`HH_RELEASE_PLAN.md`.

## Повтор инцидента 2026-10-20 — RU↔DE transport

Публичный домен штатно приходит на RU edge, но Caddy отдаёт502: German app напрямую отвечает health200, а RU relay не имеет удалённого listener19080. German `traffichub-ru-tunnel.service` постоянно получает `Connection timed out during banner exchange`. RU host capture подтверждает отправку SSH banner/KEX к DE; concurrent capture на DE не увидел этих пакетов. UFW на DE допускает established/related и порты22/2222/80/443; ban RU IP отсутствует. `sshd -t` и graceful reload RU sshd не исправили поток. Следовательно, подтверждён разрыв межсерверного пути, вероятно вне host firewall; конкретное правило внешней панели/провайдера ещё не установлено. DNS и правильную двухсерверную схему не менять.

Проверенные симптомы, конфиги, команды и границы вывода: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/EVIDENCE.md`. Runtime проверен2026-10-20; повторить smoke после восстановления inter-server connectivity.

Повторная read-only проверка 2026-10-20 14:34–14:39 UTC уточнила границу сбоя: обе стороны устанавливают TCP, но полезные данные не подтверждаются/не доходят. На DE packet capture видит RU SYN/SYN-ACK/ACK к 443 без последующего TLS payload; RU TCP stats показывают повторные передачи и `bytes_acked=1`, при host OUTPUT policy ACCEPT. DE→RU SSH получает client version, но не серверный banner. Локальный DE health остаётся200, public domain —502. Значит, это не доказанная ошибка приложения или Caddy; точный промежуточный фильтр/оператор всё ещё не определён. Обхода поверх тех же двух сетевых маршрутов не найдено: RU HTTPS relay также зависит от ответа DE origin. Не менялись runtime и пользовательские данные. Свежие evidence: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/EVIDENCE.md`.

Дополнительная проверка 2026-10-20: на обоих узлах отсутствует второй/private интерфейс, глобальный IPv6 и альтернативный route. DE→RU HTTPS: TCP connect к RU:443 проходит, TLS ClientHello отправляется, ответа нет. RIPE RDAP сопоставляет RU диапазон с `Hostkey-ZK2`, DE — с `PLAY2GO-CUSTOMERS-NETWORK`; это регистрация IP-сетей, а не подтверждение конкретного billing-аккаунта. В текущей browser session панели провайдеров не открыты. Проверки и evidence: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/EVIDENCE.md`. Следующее необходимое действие — проверка межсетевого маршрута/anti-DDoS/ACL/flow logs обеими сетями либо действующий private interconnect. Не выключать host firewalls и не менять DNS ради обхода.

На 2026-10-20 14:43 UTC публичный health остаётся502, DE-local health200, tunnel restart count199, RU:19080 не слушает. Панели HOSTKEY и PLAY2GO открыты в текущем пользовательском browser, обе остаются на login form; auth не выполнялась. TLS ClientHello DE→RU:443 также остаётся без ответа. Evidence: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/EVIDENCE.md`.

Повтор на 2026-10-20 14:45 UTC: login формы обеих панелей остаются неавторизованными; public health502, DE-local app health200, tunnel restart count207, RU listeners19080/18401 absent. Runtime не изменён. Актуальный evidence: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/EVIDENCE.md`.

Проверка 2026-10-20 14:46 UTC: public health502, DE local app200, tunnel `NRestarts=210` в auto-restart, RU forwards19080/18401 отсутствуют; хостовый OUTPUT RU ACCEPT. Панели не авторизованы. Подготовлены, не отправлены сообщения провайдерам: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/SUPPORT_REQUESTS.md`. Последние факты: `EVIDENCE.md` в той же папке.

## Авторизованные панели и повторный транспортный тест — 2026-10-20 16:49–17:00 UTC

Панели HOSTKEY и PLAY2GO авторизованы пользователем и показывают оба VPS активными. DE app health остаётся200, public RU domain502, RU relay upstream listeners19080/18401 отсутствуют; DE tunnel продолжает restart-loop (`NRestarts=249` на 17:00 UTC). RU→DE SSH/2222 теперь получает только server banner, затем KEXINIT не получает ответ; RU→DE TLS ClientHello timeout; DE→RU SSH connect проходит, но server banner не приходит. DE IP не находится в Fail2ban. Точный внешний ACL/оператор не определён.

Проверен RU-инициируемый SSH с отдельным временным forward-only доступом. KEX не завершился и listeners не появились. Временная unit, private key, DE account/authorized key и sshd drop-in удалены; `sshd -t` и reload прошли. Существующий транспорт и app не менялись. Source-прототип на `/root/TrafficHub` зафиксирован и затем отменён commits `2d019fc73`/`73ba4e5bf`; текущих runtime-следов прототипа нет. Никакие пользовательские данные и DNS не тронуты. Требуется проверка provider flow/ACL по подготовленным, но не отправленным тикетам. Evidence: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/EVIDENCE.md`.

## Самостоятельная проверка и открытые тикеты — 2026-10-20 17:26–17:32 UTC

Прямой локальный SSH в DE:22 работает, локальное приложение DE отвечает200, но RU edge остаётся502 и upstream listeners19080/18401 отсутствуют; DE reverse tunnel перезапускается (`NRestarts=351`) с таймаутом ожидания RU SSH banner. TCP handshake DE→RU на22/80/443 проходит, но HTTP-ответ и SSH banner не доходят. DE IP отсутствует в Fail2ban; текущие локальные host firewall правила не объяснили сбой.

`tracepath` показал PMTU1452; payload1424 проходит в обе стороны, 1472 превышает MTU и ожидаемо теряется. Временный узкий маршрут DE→RU MTU1300 не восстановил SSH banner и удалён после теста. Это исключает проверенный MTU обход, но не устанавливает провайдера/правило потери. Открытые тикеты: HOSTKEY CS-545988, PLAY2GO #88009; содержательного ответа пока нет. Следующий достаточный шаг — получить provider-side flow/ACL/anti-DDoS данные или использовать независимый подтверждённо рабочий канал. Текущая runtime проверка и команды: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/EVIDENCE.md`.

## Проверка наличия независимого relay — 2026-10-20 17:35 UTC

Инвентаризированы текущие SSH endpoints и работающие службы: доступны только RU `77.91.115.22` и DE `150.241.70.31`; иных SSH-узлов, VPN/overlay или relay серверов нет. DE `amn0` — disconnected Docker bridge, webhook relay — часть приложения на том же DE VPS, поэтому оба не дают независимого маршрута. Постоянный обход требует третьего узла или существующего внешнего relay. Ничего не закупалось, публичные входы/секреты не менялись. Evidence: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/EVIDENCE.md`.

## Проверенное восстановление — WireGuard RU↔DE, 2026-10-20 17:55 UTC

По просьбе пользователя не добавлять третий узел поднят прямой WireGuard overlay между существующими серверами. RU `10.254.30.1/30`, DE `10.254.30.2/30`, MTU 1392; AllowedIPs только peer /32, default route не меняется. Ключи созданы локально на серверах, private files mode 0600. DE UFW разрешает UDP/51820 только от RU; RU отбрасывает UDP/51820 с других исходных адресов.

DE `traffichub-ru-tunnel.service` теперь зависит от `wg-quick@wg0` и использует overlay для тех же ограниченных SSH remote forwards. `HostKeyAlias=77.91.115.22` сохраняет проверку известного ключа. Проверено: handshake и двусторонний ping; RU слушает только `127.0.0.1:19080` и `:18401`; RU forward health и public `https://traffic-hub.pro/api/health` вернули200; обе службы enabled/active, tunnel `NRestarts=0`. Временный UDP тестовый firewall rule/file/process удалены. Исходный провайдерский TCP payload fault не определён; приложение и данные не менялись.

Rollback: на DE удалить `10-wireguard.conf` drop-in, daemon-reload, restart tunnel service; сначала убедиться, что старый public endpoint снова работает. Overlay можно отключать только после возврата SSH target; удалять точечные правила WireGuard отдельно. Доказательства: `C:/Users/admin/Desktop/Project/outputs/traffichub-cross-server-outage-20261020/EVIDENCE.md`.
