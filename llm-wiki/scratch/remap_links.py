import os

WIKI_DIR = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\wiki"

remapping = {
    "[[польза]]": "[[элементы-сильного-текста#польза|польза]]",
    "[[честность]]": "[[элементы-сильного-текста#честность|честность]]",
    "[[конец-предложения]]": "[[элементы-сильного-текста#конец-предложения|конец-предложения]]",
    "[[правило-трех]]": "[[элементы-сильного-текста#правило-трех|правило-трех]]",
    "[[лестница-абстракции]]": "[[элементы-сильного-текста#лестница-абстракции|лестница-абстракции]]",
    "[[пассивный-залог]]": "[[элементы-сильного-текста#пассивный-залог|пассивный-залог]]",
    "[[социальное-доказательство]]": "[[элементы-сильного-текста#социальное-доказательство|социальное-доказательство]]",
    "[[конкретные-цифры]]": "[[элементы-сильного-текста#конкретные-цифры|конкретные-цифры]]",
    "[[живая-речь]]": "[[элементы-сильного-текста#живая-речь|живая-речь]]",
}

def remap_links():
    for root, _, files in os.walk(WIKI_DIR):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in remapping.items():
                    new_content = new_content.replace(old, new)
                
                if content != new_content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Remapped links in {path}")

if __name__ == "__main__":
    remap_links()
