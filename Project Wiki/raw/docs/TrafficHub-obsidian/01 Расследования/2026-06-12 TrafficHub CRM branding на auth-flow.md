## Симптом

- Пользователь попросил сделать надпись `TrafficHub` на экранах входа/регистрации такой же по цветовой схеме, как внутри dashboard.
- Дополнительно требовалось добавить приставку `CRM`.

## Зона системы

- `dashboard/index.html`
- `dashboard/style.css`
- `api/server.py`

## Гипотеза

- Экран входа использует login overlay из `dashboard/index.html`, а не отдельный auth-template.
- Экраны `register/error/callback` рендерятся из HTML-строк в `api/server.py`.
- Поэтому бренд нужно править минимум в двух местах, иначе UI разъедется.

## Проверка

- На live server подтверждено:
  - login overlay рендерит:
    - `dashboard/index.html -> <h1>TrafficHub</h1>`
  - dashboard header использует бренд:
    - `<span class="logo">Traffic<span>Hub</span></span>`
    - `dashboard/style.css`:
      - `.logo { color: var(--text) }`
      - `.logo span { color: var(--green) }`
- В `api/server.py` auth-flow имел отдельный `h1.auth-title` без split-color логики.

## Наблюдение

- На live server внесены изменения:
  - `dashboard/index.html`
    - `Traffic<span>Hub</span><strong> CRM</strong>`
  - `dashboard/style.css`
    - `login-brand span -> var(--green)`
    - `login-brand strong -> var(--text2)`
  - `api/server.py`
    - `auth-title span -> var(--green)`
    - `auth-title strong -> var(--text2)`
    - заголовки страниц обновлены до `TrafficHub CRM`
- После этого пересобран и перезапущен `autolead_server_bot`.

## Вывод

- Login screen и auth pages теперь используют ту же цветовую логику бренда, что и dashboard:
  - `Traffic` — основной текст
  - `Hub` — зелёный акцент
  - `CRM` — дополнительный suffix
- Изменение выполнено в live runtime и не ограничилось только одной страницей.

## Следующий шаг

- Если дальше будет меняться нейминг продукта, стоит вынести auth-brand markup в один shared helper вместо ручного дублирования в `dashboard/index.html` и `api/server.py`.
