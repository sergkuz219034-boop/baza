# UI polish правила TrafficHub

## Проблема

Интерфейсы TrafficHub и AccountManager развиваются точечными hotfix-ами. Без общего набора микроправил легко возвращаются визуальные дефекты: `transition: all`, скачущие числа, мелкие hit-area, тяжёлый текст и неаккуратные состояния нажатия.

## Контекст

Проект использует server-first модель: рабочий код правится на сервере в `/root/TrafficHub`. UI состоит минимум из:

- основного dashboard TrafficHub: `dashboard/style.css`;
- AccountManager dashboard: `AccountManager/dashboard/style.css`;
- AccountManager extension popup: `AccountManager/chrome-extension/popup.html`.

Skill `make-interfaces-feel-better` установлен локально в TrafServer workspace и используется как чеклист для UI-polish.

## Решение

Для UI-правок принять минимальный обязательный слой:

- не использовать `transition: all`;
- для интерактивных transitions явно перечислять свойства;
- для кнопок использовать `scale(0.96)` на active-state;
- интерактивные элементы держать не меньше `40px` по высоте;
- динамические числа показывать через `font-variant-numeric: tabular-nums`;
- заголовкам задавать `text-wrap: balance`;
- коротким текстам, подсказкам и описаниям задавать `text-wrap: pretty`;
- изображениям и аватарам давать нейтральный `outline: 1px` с pure white/black opacity, без tinted palette colors.

## Последствия

Плюсы:

- меньше визуального дрожания в карточках, таблицах и runtime-счётчиках;
- кнопки ощущаются отзывчивее без добавления JS-зависимостей;
- CSS становится предсказуемее для браузера;
- AccountManager и TrafficHub получают одинаковую базовую механику UI.

Минусы:

- это не заменяет полноценный redesign;
- новые компоненты всё равно нужно проверять по чеклисту.

## Альтернативы

- Полный редизайн дизайн-системы: лучше стратегически, но дороже и рискованнее для текущего live-продукта.
- Оставлять стили как есть: быстрее краткосрочно, но дефекты будут возвращаться в каждом новом UI-блоке.

## Подтверждение

Подтверждено на live-сервере 2026-06-26:

- изменены `dashboard/style.css`, `AccountManager/dashboard/style.css`, `AccountManager/chrome-extension/popup.html`;
- `transition: all` в целевых файлах не найден;
- пересобраны `autolead_bot` и `account_manager`;
- контейнеры `traffichub_app` и `traffichub_account_manager` поднялись `healthy`.

Повторный аудит 2026-06-30 по `make-interfaces-feel-better`:

- проверены `dashboard/style.css`, `dashboard/app.js`, `AccountManager/dashboard/style.css`;
- найден конфликт каскада: позднее правило `.table-wrap table { table-layout: fixed; }` перебивало админскую таблицу `admin-license-table`;
- исправлено в `/root/TrafficHub/dashboard/style.css`: fixed layout теперь применяется только к обычным `.table-wrap`, но не к `.admin-license-accounts`;
- админская таблица получила `table-layout: auto`, `min-width: 0` и адаптивные ширины колонок через `clamp(...)`, чтобы не появлялся внутренний горизонтальный скролл и строки не "уезжали";
- для финального слоя кнопок явно заданы `transition-duration: 0.16s` и `transition-timing-function: ease`;
- `transition: all` и `will-change: all` в `dashboard`/`AccountManager/dashboard` не найдены;
- `traffichub_app` пересобран, live `/style.css` содержит новые правила, `/api/health` вернул `status=ok`.
