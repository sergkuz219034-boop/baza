import os

WIKI_DIR = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"

def unescape_links():
    for root, _, files in os.walk(WIKI_DIR):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove common escapes that break link detection
                new_content = content.replace('\\]]', ']]').replace('\\[[', '[[').replace('\\|', '|')
                
                if content != new_content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Unescaped links in {path}")

if __name__ == "__main__":
    unescape_links()
