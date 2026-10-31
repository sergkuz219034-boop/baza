---
type: lesson
status: active
area: traffichub-hh-sheets
created: 2026-10-02
tags: [hh, sheets, timeout, checkpoint]
---

# Ошибка: timeout Sheets до открытия карточек HH

## Контекст

Одноразовый admin runner для догрузки откликов по вакансии 137675580.

## Симптом и доказательство

Первый запуск последнего отрезка завершился requests.exceptions.ReadTimeout при _open_spreadsheet / gc.open_by_key; таймаут чтения 45 секунд. Маркера PREFLIGHT нет, новые карточки резюме этим запуском не открывались. Ошибка не является доказательством ограничения HH.

## Коренная причина

Открытие workbook не завершилось в клиентский таймаут; одноразовый runner не имел ограниченного повтора этого шага. Причина задержки Google или сети не установлена.

## Исправление

До трёх попыток открытия только для requests Timeout, с небольшим увеличивающимся ожиданием. Индекс HH-ID читается из одного столбца резюме, а не всей таблицы. Запись новых лидов в базе остаётся партиями по 20; буфер записи Sheets сохраняется атомарно на сервере и восстанавливается идемпотентно.

## Профилактика (обязательное правило)

Не считать timeout Sheets исчерпанием HH-квоты и не повторять полный импорт вслепую. Разделять этапы metadata, чтения индекса, просмотра карточек, сохранения базы и выгрузки. Перед возобновлением исключать существующие ID и восстанавливать сохранённую очередь. Не делать неограниченные ретраи.

## Проверка, что ошибка не повторяется

Восстановленный запуск сохранил 66 лидов, добавил 64 строки и завершился по quota left=0. Очередь пуста, production healthy. Отдельные тесты буфера: DB20/Sheets60, retention при отказе, replay после перезапуска — PASS, без запросов HH.

## Связанный проект / эксперимент

[[../04_План/Разработка/HH admin — завершение по квоте 2026-10-02]], [[../04_План/Разработка/Эксперименты]].

## 2026-10-11 — hh_daily после полного сбора

Подтверждён повторный ReadTimeout45s в main_sheet_rows -> _open_spreadsheet после DONE complete True. Первый сбой был HH HTTP502 metadata; worker4ae8213 работал на старой версии без уже имеющегося metadata retry. Checkpoint сохранил полный сбор, повторное открытие оплаченных карточек для продолжения не требуется.

Server commit8fd840fe85a288c3c40a309fedfe48a90e667bb3 добавляет ограниченный повтор read-only main/output/provenance snapshots через существующий Sheets transient classifier и invalidation/backoff. Записи автоматически не повторяются новым wrapper.33 целевых теста прошли; read-only live-чтение обеих таблиц успешно, health200. Применение нового образа worker ожидает решения по активному циклу alex; выпуск не объявлен завершённым.

Доказательства: C:/Users/admin/Desktop/Project/outputs/hh-daily-fix-20261011/EVIDENCE.md; /root/TrafficHub/services/hh_admin_provenance.py; tests/test_hh_admin_provenance.py; worker logs11.10.2026 12:02–13:02.

Выпуск проверен 11.10.2026 19:16МСК: после явного разрешения перезапуска worker образ8fd840fe8healthy. hh_daily завершился idle/error=None за14с, без повторного HH scan. Следующий этап Check-All отклонил298 телефонов HTTP400, они сохранены; это отдельное ограничение, успешная Active-проверка не заявляется. Доказательства в той же evidence-card; pending deploy выше снят.

## 2026-10-13 — HH transport timeout и ожидание карточек
Livecheckpoint показал завершённые metadata и незавершённые cards с prior_attempt_in_24h; reservationdeadlines21:25:59/21:42:10МСК. Защита24hнеудалялась. ОтдельныйRUHHconsumerубран с externalproxyдляsignedcontrolHTTPS;safeerrorclass/HTTPstatusлогируются. Dailyсохраняетphasewaiting/resume_afterтолькоесливсенеразрешённыекарточкиожидаютreservationdeadline,metadata/poolcompleteидоставкабезошибок;невыдаётincompleteзаcompleteинеотправляетвActive. Раннийwaitingguardнепересканируетpaidcards;needs_resumeпроверяетdeadline. ИсторическаяпричинавсехHTTP502/таймаутовнеустановлена.
Commits4c23cafc7/b49d36474;25testsPASSisolatedRedis+Docker. Выпущенslimoverlayтолькоadmin_dispatcher,отдельныйRUHHconsumer;generalworkerсrunningalexнеперезапускался. Live2activeHHconnectionsGET/me200черезочередь,обаобработчикаhealthy. Ручнойсбор/анкеты/Activeне запускались;waitingstateпоявитсянаследующемштатномпродолжении. Evidence `C:/Users/admin/Desktop/Project/outputs/hh-timeout-20261013/EVIDENCE.md`,tests.txt,auth-metadata.txt,resume-window.txt.

## 2026-10-14 — ошибка RU HH в 10:32
Read-only сверка: `traffichub_hh_worker` в07:32:23.318498705Z сообщил `ConnectTimeout`; origin worker admin run10:30 упал в10:32:23 при `_request_json(resume_url)` → `hh_transport.request`. Ошибка возникла при подключении RU кHH API, конкретная сетевая первопричина не установлена. Sheets сохранил17 строк, пропустил9; затем полный цикл завершился ошибкой «Сбор HH не завершён; отправки полного цикла не запускались». Успех выгрузки Sheets не означает завершениеHH или отправку анкет. Текущиеorigin/RU workershealthy; ручныеповторы/измененияproductionневыполнялись. Доказательства: `C:/Users/admin/Desktop/Project/outputs/hh-log-check-20261014/EVIDENCE.md`; исходник `/root/TrafficHub/traffic_hub/hh_transport.py`, логиoriginworker/RUHHworker за14.10 07:25–07:40UTC.

Исправлено14.10.2026, commit `f720f188f`: RU execute повторяет только ConnectTimeout/ConnectError максимум3раз с connect8s, backoff1/2s иdeadlineguard. Read/write timeouts иHTTPответы не повторяются, paid-card protection сохранена. 6целевыхтестовPASS. Выпущен толькоRUHHconsumer (graceful restart75s), runtime/liveness/healthPASS, apphealth200; anonymousGET/me через encryptedqueue получил403 (ожидаемый отказ безавторизации), успешная авторизованная выгрузка не заявляется. Rollbacksourceсохранён рядомнаRU. Evidence `C:/Users/admin/Desktop/Project/outputs/hh-log-check-20261014/EVIDENCE.md`.

## Проверка скорости и полноты выгрузки — 2026-10-14
Read-only сверка admin за 14.10: все 282 сохранённые строки присутствуют по нормализованному контакту в pending/processed Sheets: Работа.ру 227 (autofit 201 + response 26), HH 55, missing=0. HH outbox пуст, admin idle без ошибки. Это покрытие собранных данных, не доказательство исчерпания всех upstream откликов или совпадения всех полей. Alex имеет running цикл, новых строк за проверенный день не найдено; его завершение не подтверждено.
По worker logs запуска admin 16:30: Работа.ру около48s (564 collected,14 inserted), HH около274s (18 новых контактов), две записи Sheets по6s; весь путь до конца выгрузки около5m35s. Работа.ру ожидает завершения HH перед upload. Узкое место HH: последовательные запросы с pacing2.5s через отдельную RU task/HTTP client на каждый вызов. Streamed hh_collect подготовлен, но HH_COLLECTION_EXECUTOR не задан. Большие догрузки не измерялись; upload повторно читает весь лист для dedupe/repair. Production не менялся; новые оплаченные запросы/отправки не запускались. Доказательства: `C:/Users/admin/Desktop/Project/outputs/source-upload-audit-20261014/EVIDENCE.md`, `coverage.txt`, `coverage-alex.txt`, `audit.py`; live source `/root/TrafficHub/services/hh_import.py`, `traffic_hub/hh_transport.py`, `traffic_hub/services/job_runner.py`, `modules/sheets_sync.py`.

## HH 1 секунда и параллельные owners — 2026-10-14
Пользователь разрешил уменьшить pacer и запустить реальную выгрузку. Commit `bcf83d052`: REQUEST_INTERVAL_SECONDS=1.0, 21 целевой HH test PASS, rate429/cooldown/reservation не отключены. Upload-only job admin `997899cbd1aa4eff84690ef841e87dd0` 17:32:29–17:35:49 завершён idle/errorNone: Работа.ру collected566/inserted2 (~47s); HH3 новых за~125s вместо прежних274s с18 новыми. Это разные объёмы, не контрольное сравнение speedup. Sheets +3HH,+1Работа.ру; read-only contact coverage287/287 missing0, HH outbox0. Нет429 в этом тесте.
Во время первого recreation обнаружен потерянный transient worker override и blind startup recovery, повторно захвативший live Alex job. Duplicate worker subprocess остановлен; original сохранён. Commit `187a79324` сохраняет свежие running/stopping heartbeat<180s, CAS-перемещает конкретные stale claims без удаления общего processinglist и не сбрасывает свежий owner state на startup. Persistent override сохраняет RU runtime env, enabled owners `*`, параллельный лимит0. 13 parallel/recovery/stop tests PASS, runtime future-user route/unlimited/pace1 PASS, health200; originalAlex с тем же job ID и свежим heartbeat. Legacydispatcher с активнымAlex не удалён. Внешние consumer/API лимиты остаются общими ресурсами. Полную безвредность временного duplicate по внешним sideeffects отдельно не доказали.
Evidence: `C:/Users/admin/Desktop/Project/outputs/hh-one-second-20261014/EVIDENCE.md`, `coverage.txt`; canonical `/root/TrafficHub/services/hh_import.py`, `traffic_hub/worker.py`, `traffic_hub/services/job_queue.py`, `deploy/hh-speed-20261014/worker.override.yml`.

## Alex: длительный цикл, а не подтверждённый deadlock — 2026-10-14
Проверка около19:12МСК: job982e4dab5c344209ba5728994ab4cfd3 от00:00:22 продолжает работать вlegacydispatcher. Журналvbiv_bot обновлялся19:11:44 (30строк/15мин); два read-only py-spy stack показывают `_wait_with_stop` → `run_campaign` invitation-only branch. Current delay_between_leads30s. Исходныйbacklog19062 (Sheets12777+local6285). Состояниеprogress25/12777 послеduplicateинцидента не доказываетобработкуoriginal; точныйостатокнеподтверждён. Actuallegacy `remote_autolead.enabled_for('alex')False`: oldallowlistнепонимает'*', unlike новыйgeneralworker. Остановка/перенос/изменениепаузыAlex не выполнялись. Evidence `C:/Users/admin/Desktop/Project/outputs/alex-long-run-20261014/EVIDENCE.md`; runtime `/app/modules/vbiv_bot.py:1099,1341` вtraffichub_admin_dispatcher, originalhostPID4043421.
