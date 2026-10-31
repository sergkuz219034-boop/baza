# СДВИГ — сайт zpw.su (ранее ПОЛЕ)

Проверено: 2026-10-12.

Статический сайт на RU host: `/opt/focus-group/zpw-site`. Caddy контейнер `focus-group-caddy-1` читает каталог через read-only bind `/srv/zpw-site`; блок домена в `/opt/focus-group/Caddyfile`. Правки статических файлов доступны без пересоздания сервисов.

По прямому ответу пользователя от 2026-10-12 заявки не нужно никуда отправлять. Форма удалена: раньше app.js показывал успех без сетевого запроса. Контактный блок содержит прежние Telegram, mailto и tel ссылки. Калькулятор считает 12 вариантов и переносит выбранный ориентир к контактам, данные наружу не отправляет.

Меню поддерживает Escape и наружный клик; анимация имеет паузу и reduced-motion. На ширинах 320–1440 нет горизонтального overflow. Выбор уведомления хранится в localStorage; отдельного переключателя темы нет.

Server history: `/opt/zpw-site-history`, commit `18aace93d7f7bbdcc43fa1bd3c1ad01d6872e87f`; baseline `45519ec`. Backup `/opt/focus-group/backups/zpw-polish-20261012`.

Доказательства: `C:/Users/admin/Desktop/Project/outputs/zpw-polish-20261012/EVIDENCE.md`, `live-http.json`, `deploy.log`, `live-desktop.jpg`, `live-mobile.jpg`.

Связано: [[02_Код/Эксплуатация/Доступ и подключения]], [[00_Главное/Главная/История изменений]].


## 2026-10-12 — новое позиционирование и бренд СДВИГ
Пользователь подтвердил «команда» и поручил новое название и профессиональный дизайн. Бренд заменён на СДВИГ, текущий server commit `714e38f458749cea5da120326f233cd4da5f72c6`. Прежний baseline `18aace93` сохраняется в private Git history; backup `/opt/focus-group/backups/zpw-professional-20261012`.

Главная теперь объясняет услуги через ситуацию, состав и рабочий выход; калькулятор содержит прежние 12 предварительных вариантов. Неподтверждённые анонимные отзывы удалены. Схема метода явно обозначена как пример, а не клиентский кейс. Формы/аналитика отсутствуют; notification/localStorage убраны. Прежняя строка адреса содержала «Любулица», поэтому непроверенная улица исключена, ИП/ИНН/контакты сохранены.

Дизайн: кобальт/navy/светлый холодный фон, собственный SVG знак, Golos Text локально с OFL; robots и sitemap опубликованы. Независимая визуальная проверка: SHIP после одного исправления. Targeted browser 320–1440 без overflow, calculator/menu/FAQ рабочие; десять файлов HTTP200 совпадают с candidate.

Исследование и ограничения: `C:/Users/admin/Desktop/Project/outputs/zpw-professional-20261012/RESEARCH.md`. Evidence: тот же каталог `EVIDENCE.md`, `live-http.json`, `deploy.log`, `review/verdict.md`. Конверсия и юридическая доступность имени не проверены.


## 2026-10-12 — lettering и читаемость

Release `3d8056bce5d7f2ffe0769072a73bbf89642ec601`: логотип теперь exact SVG outlines Golos720 с оптическими интервалами; заголовки550/-0.025em, body16px/1.65. Уменьшена высота hero-марки, доработан ритм мобильных блоков. Контент/JS/цены/контакты прежние. Independent visual review SHIP, type detector [], live320–1440 no overflow, HTTP200 byte match пяти изменённых файлов. Backup `/opt/focus-group/backups/zpw-type-polish-20261012`; evidence `C:/Users/admin/Desktop/Project/outputs/zpw-type-polish-20261012/EVIDENCE.md`.


## 2026-10-12 — визуальное направление отвергнуто пользователем

Пользователь отверг текущий дизайн как «нейрослоп» и запросил новое исследование красивых сайтов с анимациями. Прежний visual review SHIP подтверждал свой ограниченный scope (читаемость/нет дефектов), но не удовлетворённость пользователя. Исследованы живые Instrument, basement и Active Theory, первичные web.dev/GSAP/W3C документы. Новая рекомендация: авторская визуальная сцена, реальные работы либо явно обозначенные концепты, один focal motion и отдельная mobile-композиция. Это proposed direction, production не изменялся. Доказательства и ограничения: `C:/Users/admin/Desktop/Project/outputs/zpw-motion-research-20261012/RESEARCH.md`.


## 2026-10-12 — рабочий motion prototype

Собран hero с тремя анимируемыми материалами, визуальный разворот и tabs направлений. Концепт ФОРМА и generated предметная фотография явно обозначены демонстрационными. Local preview `http://localhost:8770/`, файлы `C:/Users/admin/Desktop/Project/outputs/zpw-motion-prototype-20261012/`. Reviewer final SHIP для показа прототипа после desktop/mobile исправлений. Основная homepage byte-exact не изменена. Шесть первоначальных файлов попали в server `motion-preview`, но финальные поправки и server commit blocked: прежний password SSH стал publickey-only, доступные ключи отвергнуты. Remote preview не считать final. Evidence EVIDENCE.md, deploy.log, review/*.jpg, chair.webp.prompt.json.


## 2026-10-12 — цельная нижняя часть prototype

После замечания пользователя «красив только начальный экран» local8770 расширен: photo/poster/site gallery, состав работ в tabs, этапы,FAQ и contact-sheet. Первый экран сохранён. Browser320–1440 no overflow;scope switch/keyboard/FAQ checked. Исправлен staleJS scope с versionwhole-20261012. Independent visual reviewSHIP только localprototype. Production не изменялся. Evidence `C:/Users/admin/Desktop/Project/outputs/zpw-motion-whole-20261012/EVIDENCE.md`.


## 2026-10-12 — пользовательский бренд ZPW

Пользователь отверг СДВИГ и мебель, указал название ZPW как в домене. Local8770 переименован по всей странице; furniture/form/chair references из HTML удалены,DOMimages0. Типографические материалы посвящены собственным услугам маркетинга,сайта иCRM. Исторические asset files не используются. Browser narrow320 fix/tabs/replay checks PASS, reviewerSHIP для localprototype. Productionнеизменён. Evidence `C:/Users/admin/Desktop/Project/outputs/zpw-brand-20261012/EVIDENCE.md`.


## 2026-10-12 — визуальные референсы ZPW

По запросу пользователя подготовлены три изображения: desktop hero, продолжение всей страницы и три мобильных экрана. Метод: встроенный image_gen; визуально проверены бренд ZPW, композиция и отсутствие отвергнутой мебели. Это предлагаемые дизайн-концепты, не опубликованный сайт и не доказательство конверсии/работы анимаций. Артефакты и спецификация: C:/Users/admin/Desktop/Project/outputs/zpw-reference-images-20261012/README.md; изображения 01-desktop.png, 02-page.png, 03-mobile.png.



## 2026-10-12 — применение референсов к production ZPW

По прямому поручению пользователя референсы перенесены в полный desktop/mobile сайт и опубликованы на https://zpw.su/. Server commit 6b689a4c30c3d87d3c31257f1144812270fd84c5; backup /opt/focus-group/backups/zpw-reference-20261012-121144/site. Статический root /opt/focus-group/zpw-site; контейнеры не пересоздавались. Версионированные CSS/JS, новая типографика и композиция всех разделов, native service/FAQ disclosures, menu Escape, direct contacts; правовые тексты сохранены. Чужой staged motion-preview не включён в commit.

Проверки: live12 файлов HTTP200/exactSHA, browser320–1440 local no overflow/live390 no overflow, menu/service keyboard/FAQ и console0. Independent visual fixes resolved; formal Impeccable automated SPEC gate открыт, pixel-identical ship не заявлен. DESIGN/sidecar обновлены по source. Evidence C:/Users/admin/Desktop/Project/outputs/zpw-reference-implementation-20261012/EVIDENCE.md; rollback.sh в том же каталоге.

