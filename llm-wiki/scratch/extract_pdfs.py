import pdfplumber
import os
import json

raw_dir = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\raw"
scratch_dir = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\scratch"
files = ["217093.pdf", "293174.pdf", "311840.pdf", "489402.pdf"]

results = {}

for file_name in files:
    file_path = os.path.join(raw_dir, file_name)
    if not os.path.exists(file_path):
        print(f"File {file_name} not found.")
        continue
    
    print(f"Processing {file_name}...")
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            results[file_name] = full_text
            
            # Save individual text files for reference
            txt_name = file_name.replace(".pdf", ".txt")
            txt_path = os.path.join(scratch_dir, txt_name)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            print(f"Extracted text saved to {txt_path}")
            
    except Exception as e:
        print(f"Error processing {file_name}: {e}")

# Save all results to a single JSON for easy reading by the agent
with open(os.path.join(scratch_dir, "extracted_texts.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
