# Operator CRM monitor drift и очистка сервера

## Симптом

Монитор каждые пять минут отправлял `CRITICAL traffichub_operator_crm missing`, хотя Operator CRM был удалён из продукта.

## Зона системы

Production systemd, Docker, deploy wrapper, GitHub Actions и воскресное обслуживание. Связано с [[Плейбук очистки production-сервера]].

## Гипотеза

Live-скрипты разошлись с каноническим checkout, а старые образы и checkout продолжили занимать диск.

## Проверка

- `/usr/local/sbin/traffichub-runtime-monitor` всё ещё содержал `traffichub_operator_crm`.
- `/usr/local/sbin/traffichub-deploy` разрешал `operator_crm`.
- Текущий `docker compose config --services`, Caddy и runtime-контейнеры Operator CRM не содержали.
- Образ `traffichub-operator_crm:latest` не использовался контейнерами.
- `/srv/traffichub-deploy` и пять `/root/TrafficHub-worktrees/*` были retired/merged и не обслуживали runtime.

## Наблюдение

Источник CRITICAL — stale live-monitor, а не падение сервиса. Перед очисткой Docker занимал 37.62 ГБ образами и 9.067 ГБ build cache; root filesystem был заполнен на 70%.

## Вывод

Operator CRM уже отсутствовал в рабочем runtime. Требовалась синхронизация установленных systemd/deploy-скриптов и удаление подтверждённо неиспользуемых артефактов. Роль доступа `operator` и исторические лиды `source=operator_crm` — отдельные данные и сохранены.

## Следующий шаг

Контролировать один цикл timer после изменений и применять [[Плейбук очистки production-сервера]] при росте диска. Не устанавливать live-скрипты вручную без синхронизации с `deploy/`.
