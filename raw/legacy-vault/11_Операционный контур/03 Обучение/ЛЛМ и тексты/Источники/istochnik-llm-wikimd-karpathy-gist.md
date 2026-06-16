---
title: "Источник: karpathy/llm-wiki.md"
type: source
tags: [source, karpathy, llm-wiki, methodology]
created: 2026-04-16
updated: 2026-04-16
url: "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f"
---

# 📄 Источник: llm-wiki.md (Karpathy gist)

**Автор**: Andrej Karpathy
**Опубликовано**: 2026-04-16
**Формат**: GitHub Gist (markdown)
**URL**: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
**Звёзды**: 5000+ | **Форков**: 4228

---

## Краткое резюме

Концептуальный документ, описывающий паттерн построения персональных баз знаний с помощью LLM. Намеренно абстрактный — описывает идею, а не конкретную реализацию.

**Центральная идея**: вместо RAG (поиск по сырым документам при каждом запросе) — LLM постепенно строит и поддерживает персистентную wiki. Знания компилируются один раз и накапливаются.

---

## Ключевые тезисы

1. **Wiki vs RAG**: wiki — компаундирующий артефакт. Перекрёстные ссылки уже есть, противоречия уже помечены, синтез уже встроен.

2. **Три слоя**: `Сырье/` (источники, неизменяемые) → `wiki/` (LLM пишет) → schema (CLAUDE.md, правила).

3. **Три операции**: Ingest (добавить источник), Query (задать вопрос), Lint (проверить здоровье).

4. **Два служебных файла**: `index.md` (контентный каталог) и `log.md` (хронологический лог).

5. **Роли**: человек курирует источники и задаёт вопросы. LLM делает всю бухгалтерию.

6. **Obsidian**: IDE для чтения. Graph View показывает структуру связей.

7. **Schema эволюционирует**: CLAUDE.md/AGENTS.md итеративно улучшается вместе с LLM.

---

## Применения из документа

| Контекст | Описание |
|---|---|
| Личное | Цели, здоровье, психология, саморазвитие |
| Исследование | Глубокое погружение в тему за недели/месяцы |
| Чтение книги | Персонажи, темы, сюжет → как фан-wiki |
| Команда | Внутренняя wiki из Slack / встреч / документов |
| Анализ | Конкуренты, due diligence, планирование, хобби |

---

## Инструменты, упомянутые в источнике

- **Obsidian** + Web Clipper: клиппинг и навигация
- **qmd**: локальный поиск по markdown (BM25 + vector)
- **Marp**: слайды из markdown
- **Dataview**: динамические таблицы из frontmatter
- **Git**: версионирование wiki

---

## Цитаты

> *«The wiki is a persistent, compounding artifact. The cross-references are already there. The contradictions have already been flagged.»*

> *«You never (or rarely) write the wiki yourself — the LLM writes and maintains all of it.»*

> *«Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase.»*

> *«The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping.»*

---

## Что не охвачено в источнике (намеренно)

Документ абстрактный — конкретная реализация зависит от домена и предпочтений:
- Точная структура директорий
- Конвенции схемы
- Форматы страниц
- Выбор инструментов

*«Правильный способ использовать это — поделиться с LLM-агентом и вместе создать версию под свои нужды.»*

---

## Связанные страницы

- [[Понятия/arkhitektura-llm-wiki|Архитектура: три слоя]]
- [[Понятия/operatsii|Операции: Ingest, Query, Lint]]
- [[Понятия/pochemu-eto-rabotaet|Почему это работает]]
- [[Сущности/andrej-karpathy|Andrej Karpathy]]
- [[Сущности/obsidian|Obsidian]]
- [[Сущности/instrumenty|Инструменты экосистемы]]

