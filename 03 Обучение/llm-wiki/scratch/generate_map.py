import os
import re
import json

wiki_dir = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"

TRANS = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def slugify(text):
    text = text.lower()
    res = ""
    for c in text:
        if 'a' <= c <= 'z' or '0' <= c <= '9':
            res += c
        elif c in TRANS:
            res += TRANS[c]
        elif c == ' ' or c == '-' or c == '_':
            res += '-'
        else:
            # Skip special chars
            pass
    res = re.sub(r'-+', '-', res).strip('-')
    return res

# 1. Parse _index.md for expected files and titles
index_path = os.path.join(wiki_dir, "_index.md")
expected_files = {} # title -> expected_rel_path_from_index
with open(index_path, "r", encoding="utf-8") as f:
    for line in f:
        match = re.search(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", line)
        if match:
            path = match.group(1).strip()
            title = match.group(2).strip() if match.group(2) else os.path.basename(path)
            expected_files[title.lower()] = path

# 2. Map all current files to titles and slugs
file_map = [] # {old_path, title, new_rel_path}
for root, dirs, files in os.walk(wiki_dir):
    for file in files:
        if not file.endswith(".md"): continue
        path = os.path.join(root, file)
        rel_path = os.path.relpath(path, wiki_dir).replace("\\", "/")
        
        # Don't rename index or log
        if file in ["_index.md", "log.md", "state.md", "overview.md"]:
            continue
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                title_meta = re.search(r"title:\s*\"?([^\"]+)\"?", content)
                
                title = ""
                if h1: title = h1.group(1).strip()
                elif title_meta: title = title_meta.group(1).strip()
                
                if not title:
                    # Fallback to filename if not broken
                    if not any(ord(c) > 127 for c in file):
                         title = os.path.splitext(file)[0]
                    else:
                         title = "unknown"
                
                new_name = slugify(title) + ".md"
                # Keep folder structure
                parent_dir = os.path.relpath(root, wiki_dir)
                if parent_dir == ".":
                    new_rel_path = new_name
                else:
                    new_rel_path = os.path.join(parent_dir, new_name).replace("\\", "/")
                
                file_map.append({
                    "old_abs": path,
                    "old_rel": rel_path,
                    "title": title,
                    "new_rel": new_rel_path
                })
        except:
            print(f"Failed to read {path}")

# 3. Handle duplicates and merge map
with open(r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\scratch\map.json", "w", encoding="utf-8") as f:
    json.dump(file_map, f, indent=2, ensure_ascii=False)

print("Map generated in c:\\Users\\Admin\\.gemini\\antigravity\\scratch\\llm-wiki\\scratch\\map.json")
