import os
import re

wiki_dir = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"
all_files = []
for root, dirs, files in os.walk(wiki_dir):
    for file in files:
        if file.endswith(".md"):
            rel_path = os.path.normpath(os.path.relpath(os.path.join(root, file), wiki_dir)).replace("\\", "/")
            all_files.append(rel_path)

# Normalize paths for matching
normalized_files = {f.lower(): f for f in all_files}

errors = []
for root, dirs, files in os.walk(wiki_dir):
    for file in files:
        if file.endswith(".md"):
            path = os.path.join(root, file)
            file_rel_path = os.path.normpath(os.path.relpath(path, wiki_dir)).replace("\\", "/")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Find [[links]]
            links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
            for link in links:
                link_target = link.strip()
                
                # Check if it's a file
                # Try as absolute from wiki root
                test_path = link_target if link_target.endswith(".md") else link_target + ".md"
                test_path = test_path.lower()
                
                found = False
                if test_path in normalized_files:
                    found = True
                else:
                    # Try relative to current file
                    current_dir = os.path.dirname(file_rel_path)
                    rel_test_path = os.path.normpath(os.path.join(current_dir, test_path)).replace("\\", "/").lower()
                    if rel_test_path in normalized_files:
                        found = True
                
                if not found:
                    errors.append(f"Broken link in {file_rel_path}: [[{link}]]")

if errors:
    print("\n".join(errors))
else:
    print("No broken links found.")
