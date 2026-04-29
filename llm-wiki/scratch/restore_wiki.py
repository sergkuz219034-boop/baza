import os
import json
import re

wiki_dir = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"
map_path = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\scratch\map.json"

with open(map_path, "r", encoding="utf-8") as f:
    file_map = json.load(f)

# Create lookup tables
# 1. Old relative path -> New relative path
rel_map = {item["old_rel"].lower(): item["new_rel"] for item in file_map}
# 2. Filename only -> New relative path (for simple [[link]] matches)
simple_map = {os.path.basename(item["old_rel"]).lower(): item["new_rel"] for item in file_map}
# 3. Title -> New relative path
title_map = {item["title"].lower(): item["new_rel"] for item in file_map}

# 1. Rename files
print("Renaming files...")
for item in file_map:
    old_abs = item["old_abs"]
    new_abs = os.path.join(wiki_dir, item["new_rel"].replace("/", "\\"))
    
    if old_abs.lower() == new_abs.lower():
        continue # Already matches (case insensitive)
        
    os.makedirs(os.path.dirname(new_abs), exist_ok=True)
    try:
        if os.path.exists(old_abs):
            # If target exists (e.g. case change), remove it first or use a temp name
            if os.path.exists(new_abs) and old_abs.lower() == new_abs.lower():
                temp_name = new_abs + ".tmp"
                os.rename(old_abs, temp_name)
                os.rename(temp_name, new_abs)
            else:
                os.rename(old_abs, new_abs)
            print(f"Renamed: {item['old_rel']} -> {item['new_rel']}")
    except Exception as e:
        print(f"Error renaming {old_abs}: {e}")

# 2. Update contents
print("Updating links in files...")
link_pattern = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")

def fix_links(content, current_file_rel):
    def replace_link(match):
        link_target = match.group(1).strip()
        display_text = match.group(2).strip() if match.group(2) else link_target
        
        # Try to find the new path for the link_target
        target_norm = link_target.lower()
        if not target_norm.endswith(".md"):
            target_norm_md = target_norm + ".md"
        else:
            target_norm_md = target_norm
            
        new_path = None
        # Check full relative path from wiki root
        if target_norm_md in rel_map:
            new_path = rel_map[target_norm_md]
        # Check simple name
        elif target_norm_md in simple_map:
            new_path = simple_map[target_norm_md]
        # Check as title
        elif target_norm in title_map:
            new_path = title_map[target_norm]
            
        if new_path:
            # Strip .md for the link
            link_display = new_path.replace(".md", "")
            return f"[[{link_display}|{display_text}]]"
        else:
            return match.group(0) # Keep as is if not found

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
                print(f"Updated links in: {rel_path}")
        except Exception as e:
            print(f"Error updating {rel_path}: {e}")

print("Restoration complete.")
