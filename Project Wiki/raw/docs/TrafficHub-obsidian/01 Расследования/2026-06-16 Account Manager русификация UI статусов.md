# 2026-06-16 Account Manager русификация UI статусов

## Симптом

В Account Manager отображались английские UI-статусы и действия:

- `ONLINE`
- `Valid`
- `Expired`
- `Auth failed`
- `Blocked`
- `Inactive`
- `Unknown`
- `Check`, `Refresh`, `Delete`, `Reconnect`, `Reauth`
- `All`

## Зона системы

- `AccountManager/dashboard/index.html`
- `AccountManager/dashboard/app.js`
- `AccountManager/dashboard/js/google.js`
- `AccountManager/dashboard/js/social.js`
- `AccountManager/dashboard/js/telegram.js`
- Docker service `account_manager`

## Гипотеза

Проблема только в frontend-labels. Внутренние status-коды (`active`, `expired`, `auth_failed`, `flood_wait`) менять нельзя, потому что они используются API, scheduler и проверками аккаунтов.

## Проверка

На сервере подтверждены английские строки через `grep -RInE` в `/root/TrafficHub/AccountManager/dashboard`.

После правки:

- source `/root/TrafficHub/AccountManager/dashboard` не содержит найденных английских UI-строк;
- контейнер `traffichub_account_manager` пересоздан из актуального image;
- внутри контейнера `/app/dashboard` не содержит найденных английских UI-строк;
- `curl http://127.0.0.1:8124/api/health` возвращает `{"status":"ok"}`;
- `/app/dashboard/index.html` содержит `В сети` вместо `ONLINE`;
- `/static/app.js` содержит русские fallback labels: `Действителен`, `Ожидание Flood Wait`, `Неизвестно`.

## Наблюдение

Первый rebuild был запущен до переноса правок в канонический `/root/TrafficHub/AccountManager`, поэтому собрал старый UI. После переноса правок в source и повторного `docker compose up -d account_manager` контейнер был пересоздан из актуального image и получил русские подписи.

## Вывод

Русификация должна оставаться на уровне UI-маппинга. Backend status-коды остаются английскими как контракт API/runtime.

## Следующий шаг

При следующих изменениях Account Manager сначала править `/root/TrafficHub/AccountManager`, а `/home/codex/accountmanager_patch` использовать только как временный staging, если он нужен.

