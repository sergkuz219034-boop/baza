import os
import pdfplumber

RAW_DIR = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\raw"
SCRATCH_DIR = r"c:\Users\Admin\.gemini\antigravity\scratch\llm-wiki\scratch"

if not os.path.exists(SCRATCH_DIR):
    os.makedirs(SCRATCH_DIR)

def extract_text_from_pdf(pdf_path, txt_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            max_pages = 100 
            for i, page in enumerate(pdf.pages):
                if i >= max_pages:
                    break
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {i+1} ---\n" + page_text
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
        return True
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return False

def main():
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".pdf")]
    for file in files:
        txt_name = file.replace(".pdf", ".txt")
        txt_path = os.path.join(SCRATCH_DIR, txt_name)
        
        if not os.path.exists(txt_path):
            print(f"Extracting {file}...")
            extract_text_from_pdf(os.path.join(RAW_DIR, file), txt_path)
        else:
            print(f"Skipping {file}, already exists.")

if __name__ == "__main__":
    main()
