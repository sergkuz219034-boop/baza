import os
import re

WIKI_DIR = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"

def get_all_md_files(directory):
    md_files = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, file), directory)
                name_no_ext = os.path.splitext(rel_path.replace("\\", "/"))[0]
                md_files[name_no_ext] = rel_path
    return md_files

def find_links(content):
    # Matches [[link]] and [[link|alias]]
    return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)

def lint_wiki():
    all_files = get_all_md_files(WIKI_DIR)
    dead_links = []
    incoming_links = {name: 0 for name in all_files}
    
    for name, rel_path in all_files.items():
        with open(os.path.join(WIKI_DIR, rel_path), 'r', encoding='utf-8') as f:
            content = f.read()
            links = find_links(content)
            for link in links:
                link_clean = link.strip().split('#')[0] # Игнорируем якорь
                if not link_clean: continue # Ссылка на тот же файл [[#якорь]]
                
                # Обработка относительных путей [[../index]]
                if link_clean.startswith("../"):
                    link_clean = link_clean[3:]
                
                found = False
                # Поиск по точному совпадению или по имени файла
                if link_clean in all_files:
                    incoming_links[link_clean] += 1
                    found = True
                else:
                    for f_name in all_files:
                        if f_name.endswith("/" + link_clean) or f_name == link_clean:
                            incoming_links[f_name] += 1
                            found = True
                            break
                            
                if not found:
                    dead_links.append((rel_path, link))

    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("### Отчет LINT")
    print("\n#### Мертвые ссылки (Target Not Found):")
    if not dead_links:
        print("Не найдено.")
    for source, target in dead_links:
        print(f"- В файле `{source}` активная ссылка `[[{target}]]` ведет в никуда.")

    print("\n#### Страницы-сироты (Zero Incoming Links):")
    # Не считаем index за сироту
    orphans = [name for name, count in incoming_links.items() if count == 0 and not name.endswith("index")]
    if not orphans:
        print("Не найдено.")
    for orphan in orphans:
        print(f"- `{all_files[orphan]}`")

if __name__ == "__main__":
    lint_wiki()
