# 2026-06-26 применение make-interfaces-feel-better к TrafficHub UI

## Симптом

Нужно установить Codex skill `jakubkrehel/make-interfaces-feel-better` и применить его к общему интерфейсу TrafficHub и AccountManager.

## Зона системы

- Серверный репозиторий: `/root/TrafficHub`
- Основной UI: `dashboard/style.css`
- AccountManager dashboard: `AccountManager/dashboard/style.css`
- AccountManager Chrome extension popup: `AccountManager/chrome-extension/popup.html`
- Runtime-контейнеры: `traffichub_app`, `traffichub_account_manager`

## Гипотеза

Минимальный безопасный эффект от skill можно получить без переписывания дизайна: убрать `transition: all`, добавить сглаживание текста, tabular numbers, text-wrap, tactile press-state и hit-area для интерактивных элементов.

## Проверка

- Skill установлен командой `npx skills add jakubkrehel/make-interfaces-feel-better`.
- Установленный путь: `C:\Users\Арт\Desktop\TrafServer\.agents\skills\make-interfaces-feel-better`.
- На сервере проверено наличие проблемных CSS-паттернов через поиск `transition:\s*all|will-change:\s*all`.
- После правок пересобраны только сервисы `autolead_bot` и `account_manager`.

## Наблюдение

В `AccountManager/dashboard/style.css` был подтверждённый дефект: `--transition: all 0.16s ease`.

В `dashboard/style.css` часть правил уже была применена ранее: root font smoothing, `text-wrap`, `font-variant-numeric`, press-scale для кнопок.

## Вывод

На live-сервере применён общий UI-polish слой:

- `transition: all` заменён на явный список свойств;
- динамические числа получают `font-variant-numeric: tabular-nums`;
- заголовки получают `text-wrap: balance`;
- короткие описания получают `text-wrap: pretty`;
- кнопки и интерактивные элементы получают минимум `40px` высоты и `scale(0.96)` при нажатии;
- изображения и аватары получают нейтральный `outline` без влияния на layout.

Контейнеры после пересборки: `traffichub_app` и `traffichub_account_manager` поднялись в состоянии `healthy`.

## Следующий шаг

При следующих UI-задачах сверяться с [[UI polish правила TrafficHub]] и не возвращать `transition: all`.

