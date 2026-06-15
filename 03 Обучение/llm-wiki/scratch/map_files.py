import os
import re

wiki_dir = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"
all_info = []

for root, dirs, files in os.walk(wiki_dir):
    for file in files:
        if file.endswith(".md"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    title = re.search(r"title:\s*\"?([^\"]+)\"?", content)
                    
                    found_title = ""
                    if h1: found_title = h1.group(1).strip()
                    elif title: found_title = title.group(1).strip()
                    
                    all_info.append({
                        "path": path,
                        "rel_path": os.path.relpath(path, wiki_dir),
                        "found_title": found_title
                    })
            except Exception as e:
                pass

for info in all_info:
    print(f"File: {info['rel_path']} | Title: {info['found_title']}")
