import os
import json
import re

wiki_dir = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"
map_path = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\scratch\map.json"

with open(map_path, "r", encoding="utf-8") as f:
    file_map = json.load(f)

# Create lookup tables
rel_map = {item["old_rel"].lower(): item["new_rel"] for item in file_map}
simple_map = {os.path.basename(item["old_rel"]).lower(): item["new_rel"] for item in file_map}
title_map = {item["title"].lower(): item["new_rel"] for item in file_map}

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
            pass
    res = re.sub(r'-+', '-', res).strip('-')
    return res

link_pattern = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")

def fix_links(content, current_file_rel):
    def replace_link(match):
        full_target = match.group(1).strip()
        display_text = match.group(2).strip() if match.group(2) else full_target
        
        # Split anchor
        if "#" in full_target:
            parts = full_target.split("#", 1)
            link_target, anchor = parts[0], "#" + parts[1]
        else:
            link_target, anchor = full_target, ""
            
        if not link_target: # [[#anchor]]
            return f"[[{anchor}|{display_text}]]"
            
        target_norm = link_target.lower()
        if not target_norm.endswith(".md"):
            target_norm_md = target_norm + ".md"
        else:
            target_norm_md = target_norm
            
        new_path = None
        if target_norm_md in rel_map:
            new_path = rel_map[target_norm_md]
        elif target_norm_md in simple_map:
            new_path = simple_map[target_norm_md]
        elif target_norm in title_map:
            new_path = title_map[target_norm]
        elif target_norm_md == "../index.md" or target_norm == "../index":
            new_path = "_index.md"
        elif target_norm == "index":
            new_path = "_index.md"
            
        if new_path:
            link_display = new_path.replace(".md", "")
            return f"[[{link_display}{anchor}|{display_text}]]"
        else:
            # Try slugifying to match current file
            current_base = os.path.basename(current_file_rel).replace(".md", "").lower()
            if slugify(link_target) == current_base:
                 return f"[[#{anchor if anchor else ''}|{display_text}]]".replace("[[#|", "[[#")
            return match.group(0)

    return link_pattern.sub(replace_link, content)

for root, dirs, files in os.walk(wiki_dir):
    for file in files:
        if not file.endswith(".md"): continue
        path = os.path.join(root, file)
        rel_path = os.path.relpath(path, wiki_dir).replace("\\", "/")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = fix_links(content, rel_path)
            
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Refined links in: {rel_path}")
        except Exception as e:
            print(f"Error updating {rel_path}: {e}")

print("Refinement complete.")
