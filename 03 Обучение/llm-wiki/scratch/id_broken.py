import os
import re

wiki_dir = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"
broken_files = []

for root, dirs, files in os.walk(wiki_dir):
    for file in files:
        if "" in file:
            broken_files.append(os.path.join(root, file))

for bf in broken_files:
    try:
        with open(bf, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if match:
                print(f"Path: {bf}")
                print(f"H1: {match.group(1).strip()}")
            else:
                # Try to find title in metadata
                match = re.search(r"title:\s*\"?([^\"]+)\"?", content)
                if match:
                     print(f"Path: BF: {bf}")
                     print(f"Title: {match.group(1).strip()}")
                else:
                    print(f"Path: {bf} - NO TITLE FOUND")
    except Exception as e:
        print(f"Error reading {bf}: {e}")
