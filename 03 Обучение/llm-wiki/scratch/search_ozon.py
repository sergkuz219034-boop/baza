import os
import glob

search_terms = ["Ozon", "Озон"]
files = glob.glob("scratch/*.txt")

for file_path in files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            for term in search_terms:
                if term.lower() in content.lower():
                    print(f"FOUND '{term}' in {file_path}")
                    # Print context
                    idx = content.lower().find(term.lower())
                    start = max(0, idx - 100)
                    end = min(len(content), idx + 200)
                    print(f"Context: ...{content[start:end]}...")
                    print("-" * 40)
    except Exception as e:
        pass
