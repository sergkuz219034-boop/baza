import os
import re

WIKI_DIR = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"

def fix_links():
    for root, _, files in os.walk(WIKI_DIR):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace [[../anything/name]] with [[name]]
                # Also handle aliases [[../anything/name|alias]]
                new_content = re.sub(r'\[\[\.\./[^/|]+/([^\]|]+)', r'[[\1', content)
                
                # Special case for index in synthesis/index.md or similar
                new_content = new_content.replace('[[../index]]', '[[index]]')
                
                # Fix trailing slashes in links like [[ai-detection-deep-dive\]] (often found in logs/indices)
                new_content = new_content.replace('\]]', ']]')

                if content != new_content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Fixed links in {path}")

if __name__ == "__main__":
    fix_links()
